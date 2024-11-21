from typing import Dict, List
from .airtable_client import AirtableClient
from database.postgresql import PostgresClient


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
            "singleLineText": "VARCHAR(255)",
            "multilineText": "TEXT",
            "email": "VARCHAR(255)",
            "url": "VARCHAR(255)",
            "checkbox": "BOOLEAN",
            "date": "DATE",
            "dateTime": "TIMESTAMP",
            "number": "NUMERIC",
            "currency": "NUMERIC",
            "singleSelect": "VARCHAR(255)",
            "multipleSelects": "TEXT[]",
            "multipleRecordLinks": "INTEGER[]",
            "formula": "VARCHAR(255)",
            "richText": "TEXT",
            "autoNumber": "SERIAL",
            "createdTime": "TIMESTAMP",
            "lastModifiedTime": "TIMESTAMP",
            "count": "INTEGER",
            "phone": "VARCHAR(50)",
            "rating": "INTEGER",
            "duration": "INTERVAL",
            "barcode": "VARCHAR(255)"
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

    def create_table(self, table_name: str, fields: List[Dict]) -> None:
        """
        Tworzy nową tabelę w PostgreSQL.
        
        Args:
            table_name: Nazwa tabeli
            fields: Lista pól z ich typami i opcjami
        """
        field_definitions = []
        
        # Zawsze dodajemy pole id jako PRIMARY KEY
        field_definitions.append("id SERIAL PRIMARY KEY")
        field_definitions.append("airtable_id VARCHAR(255) UNIQUE")
        
        for field in fields:
            field_type = self.type_mapping.get(field['type'], 'TEXT')
            field_name = field['name'].lower().replace(' ', '_')
            field_def = f"{field_name} {field_type}"
            field_definitions.append(field_def)

        # Dodajemy metadane
        field_definitions.extend([
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        ])

        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {self.postgres.schema}.{table_name} (
                {', '.join(field_definitions)}
            )
        """
        
        self.postgres.execute_modification(create_table_sql)
        
        # Tworzymy trigger do automatycznej aktualizacji updated_at
        trigger_sql = f"""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';

            DROP TRIGGER IF EXISTS update_updated_at_trigger ON {self.postgres.schema}.{table_name};
            
            CREATE TRIGGER update_updated_at_trigger
                BEFORE UPDATE ON {self.postgres.schema}.{table_name}
                FOR EACH ROW
                EXECUTE FUNCTION update_updated_at_column();
        """
        self.postgres.execute_modification(trigger_sql)

    def sync_schema(self, base_id: str) -> None:
        """
        Synchronizuje schemat bazy Airtable z PostgreSQL.
        
        Args:
            base_id: ID bazy Airtable do zsynchronizowania
        """
        # Pobierz schemat z Airtable
        airtable_schema = self.airtable.get_base_schema(base_id)
        existing_tables = self.get_postgres_tables()
        
        base_name = airtable_schema['name'].lower().replace(' ', '_')
        
        for table in airtable_schema['tables']:
            # Tworzymy nazwę tabeli w formacie: nazwa_bazy_nazwa_tabeli
            pg_table_name = f"{base_name}_{table['name'].lower().replace(' ', '_')}"
            
            if pg_table_name not in existing_tables:
                print(f"Tworzenie tabeli: {pg_table_name}")
                self.create_table(pg_table_name, table['fields'])
            else:
                print(f"Tabela {pg_table_name} już istnieje") 