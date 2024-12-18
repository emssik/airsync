import os
import yaml
from dotenv import load_dotenv
from emsairtable.airtable_client import AirtableClient
from emsairtable.schema_sync import SchemaSync
from emsairtable.data_sync import DataSync
from database.postgresql import PostgresClient

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def main():
    # Wczytaj zmienne środowiskowe i konfigurację
    load_dotenv()
    config = load_config()
    
    # Konfiguracja Airtable
    airtable_api_key = os.getenv('AIRTABLE_API_KEY')
    mentoring_base_id = 'appwySEDDNDEYSvoW'
    
    if not airtable_api_key:
        raise ValueError("Brak wymaganej zmiennej środowiskowej AIRTABLE_API_KEY")
    
    # Konfiguracja PostgreSQL z pliku config.yaml
    pg_config = {
        'host': config['database']['host'],
        'port': str(config['database']['port']),
        'database_name': config['database']['database_name'],
        'user': config['database']['user'],
        'password': os.getenv('POSTGRESQL_PASSWORD'),
        'schema': os.getenv('POSTGRES_SCHEMA', 'public')
    }
    
    if not pg_config['password']:
        raise ValueError("Brak wymaganej zmiennej środowiskowej POSTGRESQL_PASSWORD")

    postgres_client = None
    try:
        # Inicjalizacja klientów
        print("Inicjalizacja klientów...")
        airtable_client = AirtableClient(airtable_api_key)
        postgres_client = PostgresClient(pg_config)
        
        # Inicjalizacja synchronizatorów
        schema_sync = SchemaSync(airtable_client, postgres_client)
        data_sync = DataSync(airtable_client, postgres_client)
        
        # Pobierz i wyświetl informacje o bazie przed synchronizacją
        print("\nInformacje o bazie Mentoring:")
        base_schema = airtable_client.get_base_schema(mentoring_base_id)
        print(f"Nazwa bazy: {base_schema['name']}")
        print(f"Liczba tabel: {len(base_schema['tables'])}")
        print("Tabele:")
        for table in base_schema['tables']:
            print(f"- {table['name']} ({len(table['fields'])} pól)")
        
        # Synchronizacja schematu
        print("\nRozpoczynam synchronizację schematu...")
        schema_sync.sync_schema(mentoring_base_id)
        print("Synchronizacja schematu zakończona pomyślnie!")
        
        # Synchronizacja danych
        print("\nRozpoczynam synchronizację danych...")
        try:
            data_sync.sync_base_data(mentoring_base_id)
            print("Synchronizacja danych zakończona pomyślnie!")
        except Exception as e:
            print(f"\nBłąd podczas synchronizacji danych: {str(e)}")
            raise  # Przerwij działanie po pierwszym błędzie
        
        # Wyświetl listę tabel w PostgreSQL po synchronizacji
        print("\nTabele w PostgreSQL po synchronizacji:")
        postgres_tables = schema_sync.get_postgres_tables()
        for table in postgres_tables:
            print(f"- {table}")
        
    except Exception as e:
        print(f"\nWystąpił krytyczny błąd: {str(e)}")
        raise  # Przerwij działanie programu
    finally:
        if postgres_client:
            postgres_client.close()

if __name__ == "__main__":
    main() 