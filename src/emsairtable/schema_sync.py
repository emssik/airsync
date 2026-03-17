from typing import Dict, List
from .airtable_client import AirtableClient
from database.postgresql import PostgresClient
from psycopg2 import sql

_RESERVED_WORDS = frozenset({
    "check", "user", "select", "from", "where", "insert", "update", "delete", "do",
    "order", "group", "table", "index", "type", "name", "value", "key", "primary",
    "default", "create", "drop", "alter", "column", "limit", "offset", "between",
    "having", "join", "left", "right", "inner", "outer", "on", "as", "and", "or",
    "not", "in", "is", "null", "true", "false", "case", "when", "then", "else",
    "end", "like", "exists", "all", "any", "distinct", "set", "into", "values",
    "return", "begin", "commit", "rollback", "transaction", "trigger", "view",
    "function", "procedure", "schema", "database", "constraint", "unique",
    "foreign", "references", "cascade", "sequence", "grant", "revoke",
})


class SchemaSync:
    def __init__(self, airtable_client: AirtableClient, postgres_client: PostgresClient):
        """
        Inicjalizuje synchronizator schematów.

        Args:
            airtable_client: Instancja klienta Airtable
            postgres_client: Instancja klienta PostgreSQL
        """
        self.airtable = airtable_client
        self.postgres = postgres_client
        self.type_mapping = {
            # Surowe typy Airtable
            "singleLineText": "TEXT",
            "multilineText": "TEXT",
            "richText": "TEXT",
            "email": "TEXT",
            "url": "TEXT",
            "phoneNumber": "TEXT",
            "checkbox": "BOOLEAN",
            "date": "DATE",
            "dateTime": "TIMESTAMP",
            "number": "NUMERIC",
            "currency": "NUMERIC",
            "percent": "NUMERIC",
            "singleSelect": "TEXT",
            "multipleSelects": "TEXT",
            "multipleRecordLinks": "TEXT",
            "multipleAttachments": "TEXT",
            "formula": "TEXT",
            "rollup": "TEXT",
            "lookup": "TEXT",
            "autoNumber": "SERIAL",
            "createdTime": "TIMESTAMP",
            "lastModifiedTime": "TIMESTAMP",
            "count": "INTEGER",
            "rating": "INTEGER",
            "duration": "INTERVAL",
            "barcode": "TEXT",
            # Znormalizowane typy (kompatybilność wsteczna)
            "phone": "TEXT",
        }

    def get_postgres_tables(self) -> List[str]:
        """Pobiera listę istniejących tabel w PostgreSQL."""
        query = """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
        """
        results = self.postgres.execute_query(query, (self.postgres.schema,))
        return [row['table_name'] for row in results]

    def resolve_columns(self, fields: list) -> list:
        """Zwraca listę unikalnych nazw kolumn z deduplikacją, ta sama logika co create_table."""
        used_names = {'airtable_id', 'created_at', 'updated_at'}
        resolved = []
        for field in fields:
            name = self.clean_name(field['name'])
            base = name
            counter = 1
            while name in used_names:
                name = f"{base}_{counter}"
                counter += 1
            used_names.add(name)
            resolved.append(name)
        return resolved

    def create_table(self, table_name: str, fields: List[Dict]) -> None:
        """
        Tworzy nową tabelę w PostgreSQL.

        Args:
            table_name: Nazwa tabeli
            fields: Lista pól z ich typami i opcjami
        """
        # Używamy airtable_id jako PRIMARY KEY zamiast dodatkowego id
        field_sql_parts = [sql.SQL("airtable_id TEXT PRIMARY KEY")]

        resolved_names = self.resolve_columns(fields)
        for field, field_name in zip(fields, resolved_names):
            field_type = self.type_mapping.get(field['type'], 'TEXT')
            field_sql_parts.append(
                sql.SQL("{} {}").format(
                    sql.Identifier(field_name),
                    sql.SQL(field_type)
                )
            )

        # Dodajemy metadane
        field_sql_parts.append(sql.SQL("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
        field_sql_parts.append(sql.SQL("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))

        create_sql = sql.SQL("CREATE TABLE IF NOT EXISTS {schema}.{table} ({fields})").format(
            schema=sql.Identifier(self.postgres.schema),
            table=sql.Identifier(table_name),
            fields=sql.SQL(", ").join(field_sql_parts)
        )

        self.postgres.execute_modification(create_sql)

        # Tworzymy trigger do automatycznej aktualizacji updated_at
        trigger_func_sql = sql.SQL("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql'
        """)
        self.postgres.execute_modification(trigger_func_sql)

        drop_trigger_sql = sql.SQL(
            "DROP TRIGGER IF EXISTS update_updated_at_trigger ON {schema}.{table}"
        ).format(
            schema=sql.Identifier(self.postgres.schema),
            table=sql.Identifier(table_name)
        )
        self.postgres.execute_modification(drop_trigger_sql)

        create_trigger_sql = sql.SQL(
            "CREATE TRIGGER update_updated_at_trigger"
            " BEFORE UPDATE ON {schema}.{table}"
            " FOR EACH ROW"
            " EXECUTE FUNCTION update_updated_at_column()"
        ).format(
            schema=sql.Identifier(self.postgres.schema),
            table=sql.Identifier(table_name)
        )
        self.postgres.execute_modification(create_trigger_sql)

    def clean_name(self, name: str) -> str:
        """
        Czyści nazwę z niedozwolonych znaków dla PostgreSQL.

        Args:
            name: Nazwa do wyczyszczenia
        Returns:
            Oczyszczona nazwa
        """
        cleaned = name.lower()
        cleaned = cleaned.replace('.', '_').replace(' ', '_').replace('-', '_')
        cleaned = ''.join(c for c in cleaned if c.isalnum() or c == '_')

        if cleaned and cleaned[0].isdigit():
            cleaned = f'col_{cleaned}'

        if cleaned in _RESERVED_WORDS:
            cleaned = f'{cleaned}_field'

        return cleaned

    def sync_schema(self, base_id: str, base_schema: Dict = None) -> None:
        """
        Synchronizuje schemat bazy Airtable z PostgreSQL.

        Args:
            base_id: ID bazy Airtable do zsynchronizowania
            base_schema: Opcjonalny wcześniej pobrany schemat bazy (unika zbędnego wywołania API)
        """
        airtable_schema = base_schema if base_schema is not None else self.airtable.get_base_schema(base_id)
        existing_tables = self.get_postgres_tables()

        base_name = self.clean_name(airtable_schema['name'])

        for table in airtable_schema['tables']:
            # Tworzymy nazwę tabeli w formacie: nazwa_bazy_nazwa_tabeli
            table_name = self.clean_name(table['name'])
            pg_table_name = f"{base_name}_{table_name}"

            if pg_table_name not in existing_tables:
                print(f"Tworzenie tabeli: {pg_table_name}")
                self.create_table(pg_table_name, table['fields'])
            else:
                print(f"Tabela {pg_table_name} już istnieje")
