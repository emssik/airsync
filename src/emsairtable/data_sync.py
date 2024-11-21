from typing import Dict, List, Any
from datetime import datetime
import json
from .airtable_client import AirtableClient
from database.postgresql import PostgresClient
from .schema_sync import SchemaSync

class DataSync:
    def __init__(self, airtable_client: AirtableClient, postgres_client: PostgresClient):
        """
        Inicjalizuje synchronizator danych.
        
        Args:
            airtable_client: Instancja klienta Airtable
            postgres_client: Instancja klienta PostgreSQL
        """
        self.airtable = airtable_client
        self.postgres = postgres_client
        self.schema_sync = SchemaSync(airtable_client, postgres_client)

    def _convert_value(self, value: Any, field_type: str) -> Any:
        """
        Konwertuje wartość z Airtable na odpowiedni typ PostgreSQL.
        """
        if value is None:
            return None
            
        if isinstance(value, list):
            # Dla list (np. multipleSelects, multipleRecordLinks)
            try:
                return json.dumps(value, ensure_ascii=False)
            except Exception:
                return '[]'
            
        if field_type in ['date', 'dateTime']:
            try:
                if 'T' in str(value):  # Format ISO z czasem
                    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                return datetime.strptime(str(value), '%Y-%m-%d').date()
            except ValueError:
                return None
                
        if field_type == 'number':
            try:
                return float(value) if '.' in str(value) else int(value)
            except (ValueError, TypeError):
                return None
                
        if field_type == 'checkbox':
            return bool(value)
            
        # Dla wszystkich typów tekstowych po prostu zwracamy string
        return str(value)

    def _batch_upsert_records(self, pg_table_name: str, records: List[Dict], table_schema: Dict) -> None:
        """
        Wsadowo wstawia lub aktualizuje rekordy w PostgreSQL.
        """
        if not records:
            return

        # Stwórz mapowanie nazw pól na typy
        field_types = {
            field['name']: field['type']
            for field in table_schema['fields']
        }

        # Pobierz wszystkie możliwe kolumny z wszystkich rekordów
        all_fields = set()
        for record in records:
            all_fields.update(record['fields'].keys())
        all_fields.add('airtable_id')

        # Przygotuj listę kolumn (oczyszczone nazwy)
        columns = [self.schema_sync.clean_name(k) for k in all_fields]
        
        # Przygotuj wartości dla wszystkich rekordów
        values_list = []
        for record in records:
            fields = record['fields'].copy()
            fields['airtable_id'] = record['id']
            
            # Konwertuj wartości na odpowiednie typy
            row_values = []
            for field_name in all_fields:
                value = fields.get(field_name)
                field_type = field_types.get(field_name, 'text')
                converted_value = self._convert_value(value, field_type)
                row_values.append(converted_value)
                
            values_list.append(row_values)

        # Przygotuj zapytanie UPSERT
        placeholders = [f'%s' for _ in range(len(columns))]
        columns_str = ', '.join(columns)
        placeholders_str = ', '.join(placeholders)
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in columns if col != 'airtable_id'])

        upsert_query = f"""
            INSERT INTO {self.postgres.schema}.{pg_table_name} ({columns_str})
            VALUES ({placeholders_str})
            ON CONFLICT (airtable_id) 
            DO UPDATE SET {update_str}
        """

        # Wykonaj wsadowe upsert dla każdego rekordu
        for values in values_list:
            self.postgres.execute_modification(upsert_query, values)

    def _update_column_types(self, pg_table_name: str, records: List[Dict]) -> None:
        """
        Aktualizuje typy kolumn w PostgreSQL na TEXT dla kolumn zawierających długie teksty.
        """
        # Znajdź kolumny zawierające długie teksty
        long_text_columns = set()
        for record in records:
            for field_name, value in record['fields'].items():
                if isinstance(value, str) and len(value) > 255:
                    clean_name = self.schema_sync.clean_name(field_name)
                    long_text_columns.add(clean_name)

        # Zmień typ kolumn na TEXT
        for column in long_text_columns:
            alter_query = f"""
                ALTER TABLE {self.postgres.schema}.{pg_table_name} 
                ALTER COLUMN {column} TYPE TEXT;
            """
            try:
                self.postgres.execute_modification(alter_query)
                print(f"Zmieniono typ kolumny {column} na TEXT")
            except Exception as e:
                print(f"Nie udało się zmienić typu kolumny {column}: {str(e)}")

    def sync_table_data(self, base_id: str, table_name: str) -> None:
        """
        Synchronizuje dane z jednej tabeli Airtable do PostgreSQL.
        """
        base_schema = self.airtable.get_base_schema(base_id)
        base_name = self.schema_sync.clean_name(base_schema['name'])
        pg_table_name = f"{base_name}_{self.schema_sync.clean_name(table_name)}"

        # Znajdź schemat tabeli
        table_schema = next(
            (table for table in base_schema['tables'] if table['name'] == table_name),
            None
        )
        if not table_schema:
            raise ValueError(f"Nie znaleziono schematu dla tabeli {table_name}")

        records = self.airtable.get_table_records(base_id, table_name)
        print(f"Pobrano {len(records)} rekordów z tabeli {table_name}")

        # Dodane: Aktualizuj typy kolumn przed wstawieniem danych
        self._update_column_types(pg_table_name, records)

        batch_size = 10
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self._batch_upsert_records(pg_table_name, batch, table_schema)
            print(f"Zsynchronizowano {i + len(batch)} z {len(records)} rekordów")

    def sync_base_data(self, base_id: str) -> None:
        """
        Synchronizuje dane wszystkich tabel z bazy Airtable do PostgreSQL.
        """
        base_schema = self.airtable.get_base_schema(base_id)
        
        for table in base_schema['tables']:
            print(f"\nSynchronizacja danych tabeli: {table['name']}")
            self.sync_table_data(base_id, table['name']) 