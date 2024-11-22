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
        Wszystkie referencje do innych rekordów są zapisywane jako JSON string.
        """
        if value is None:
            return None
        
        if isinstance(value, list):
            # Wszystkie listy (łącznie z linkami do innych rekordów) zapisujemy jako JSON
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
        
        # Wszystko inne jako tekst
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
            try:
                self.postgres.execute_modification(upsert_query, values)
            except Exception as e:
                print("\nWystąpił błąd podczas wstawiania rekordu. Szczegóły:")
                print(f"Tabela: {pg_table_name}")
                print("\nMapowanie kolumn na wartości:")
                for col, val in zip(columns, values):
                    print(f"{col}: {val} (typ Python: {type(val).__name__})")
                print("\nTypy pól z Airtable:")
                for field_name in all_fields:
                    field_type = field_types.get(field_name, 'text')
                    print(f"{field_name}: {field_type}")
                print(f"\nZapytanie SQL:\n{upsert_query}")
                print(f"\nBłąd: {str(e)}")
                raise

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