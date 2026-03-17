from typing import Dict, List, Any
from datetime import datetime
import json
from psycopg2 import sql
from .airtable_client import AirtableClient
from database.postgresql import PostgresClient
from .schema_sync import SchemaSync


class DataSync:
    def __init__(self, airtable_client: AirtableClient, postgres_client: PostgresClient, schema_sync=None):
        """
        Inicjalizuje synchronizator danych.

        Args:
            airtable_client: Instancja klienta Airtable
            postgres_client: Instancja klienta PostgreSQL
            schema_sync: Opcjonalna instancja SchemaSync (dependency injection)
        """
        self.airtable = airtable_client
        self.postgres = postgres_client
        self.schema_sync = schema_sync if schema_sync is not None else SchemaSync(airtable_client, postgres_client)

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

    def _batch_upsert_records(
        self,
        pg_table_name: str,
        records: List[Dict],
        all_fields: List[str],
        field_types: Dict[str, str],
        upsert_query,
    ) -> None:
        """Wsadowo wstawia lub aktualizuje rekordy w PostgreSQL."""
        if not records:
            return

        values_list = []
        for record in records:
            row_values = []
            for field_name in all_fields:
                value = record['id'] if field_name == 'airtable_id' else record['fields'].get(field_name)
                row_values.append(self._convert_value(value, field_types.get(field_name, 'text')))
            values_list.append(tuple(row_values))

        try:
            self.postgres.execute_many(upsert_query, values_list)
        except Exception as e:
            print("\nWystąpił błąd podczas wsadowego wstawiania rekordów. Szczegóły:")
            print(f"Tabela: {pg_table_name}")
            print(f"Typy pól: { {k: field_types.get(k, 'text') for k in all_fields} }")
            print(f"Błąd: {str(e)}")
            raise

    def sync_table_data(self, base_id: str, table_name: str, base_schema: dict = None) -> None:
        """
        Synchronizuje dane z jednej tabeli Airtable do PostgreSQL.
        """
        if base_schema is None:
            base_schema = self.airtable.get_base_schema(base_id)
        base_name = self.schema_sync.clean_name(base_schema['name'])
        pg_table_name = f"{base_name}_{self.schema_sync.clean_name(table_name)}"

        table_schema = next(
            (table for table in base_schema['tables'] if table['name'] == table_name),
            None
        )
        if not table_schema:
            raise ValueError(f"Nie znaleziono schematu dla tabeli {table_name}")

        # Oblicz raz per tabela: mapowanie nazw i zapytanie UPSERT
        schema_fields = table_schema['fields']
        resolved_names = self.schema_sync.resolve_columns(schema_fields)
        # Mapowanie po indeksie — nazwy oryginalne mogą się powtarzać
        all_fields = ['airtable_id'] + [f['name'] for f in schema_fields]
        columns = ['airtable_id'] + resolved_names
        field_types = {f['name']: f['type'] for f in schema_fields}

        col_identifiers = [sql.Identifier(c) for c in columns]
        update_parts = [
            sql.SQL("{col} = EXCLUDED.{col}").format(col=sql.Identifier(c))
            for c in columns if c != 'airtable_id'
        ]
        upsert_query = sql.SQL(
            "INSERT INTO {schema}.{table} ({cols})"
            " VALUES ({placeholders})"
            " ON CONFLICT (airtable_id)"
            " DO UPDATE SET {updates}"
        ).format(
            schema=sql.Identifier(self.postgres.schema),
            table=sql.Identifier(pg_table_name),
            cols=sql.SQL(", ").join(col_identifiers),
            placeholders=sql.SQL(", ").join(sql.SQL("%s") for _ in columns),
            updates=sql.SQL(", ").join(update_parts),
        )

        records = self.airtable.get_table_records(base_id, table_name)
        print(f"Pobrano {len(records)} rekordów z tabeli {table_name}")

        batch_size = 10
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            self._batch_upsert_records(pg_table_name, batch, all_fields, field_types, upsert_query)
            print(f"Zsynchronizowano {i + len(batch)} z {len(records)} rekordów")

    def sync_base_data(self, base_id: str, base_schema: dict = None) -> None:
        """
        Synchronizuje dane wszystkich tabel z bazy Airtable do PostgreSQL.
        """
        if base_schema is None:
            base_schema = self.airtable.get_base_schema(base_id)

        for table in base_schema['tables']:
            print(f"\nSynchronizacja danych tabeli: {table['name']}")
            self.sync_table_data(base_id, table['name'], base_schema=base_schema)
