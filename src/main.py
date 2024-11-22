from dotenv import load_dotenv
import os
import time
import yaml
from emsairtable.airtable_client import AirtableClient
from emsairtable.schema_printer import SchemaPrinter
from emsairtable.schema_sync import SchemaSync
from emsairtable.data_sync import DataSync
from database.postgresql import PostgresClient

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def main():
    """Główna funkcja programu synchronizująca wszystkie dostępne bazy Airtable z PostgreSQL"""
    # Wczytaj zmienne środowiskowe i konfigurację
    load_dotenv()
    config = load_config()
    
    # Konfiguracja Airtable
    AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
    
    if not AIRTABLE_API_KEY:
        print("Błąd: Brak klucza API Airtable")
        return

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
        print("=== Start programu ===")
        start_time = time.time()
        
        # Inicjalizacja klientów
        print("\n1. Inicjalizacja połączenia z Airtable i PostgreSQL...")
        airtable_client = AirtableClient(AIRTABLE_API_KEY)
        postgres_client = PostgresClient(pg_config)
        
        # Inicjalizacja synchronizatorów
        schema_sync = SchemaSync(airtable_client, postgres_client)
        data_sync = DataSync(airtable_client, postgres_client)
        
        # Pobierz wszystkie bazy
        print("\n2. Pobieranie listy baz...")
        bases = airtable_client.list_bases()
        bases_time = time.time()
        print(f"Znaleziono {len(bases)} baz danych:")
        for base_id, base_name in bases.items():
            print(f"- {base_name} (ID: {base_id})")
        print(f"Czas pobierania listy baz: {bases_time - start_time:.2f} sekund")

        total_tables = 0
        processed_bases = 0
        
        # Iteruj przez wszystkie bazy
        for base_id, base_name in bases.items():
            print(f"\n=== Przetwarzanie bazy: {base_name} ===")
            print(f"ID bazy: {base_id}")
            
            try:
                # Pobierz schemat bazy
                print(f"3. Pobieranie schematu bazy {base_name}...")
                schema = airtable_client.get_base_schema(base_id)
                print("Otrzymany schemat:")
                print(f"Schema: {schema}")
                print(f"Znaleziono {len(schema['tables'])} tabel w bazie")
                total_tables += len(schema['tables'])
                
                print("\n4. Szczegółowy schemat bazy:")
                print("Tabele:")
                for table in schema['tables']:
                    print(f"  - Nazwa tabeli: {table['name']}")
                    print("    Pola:")
                    for field in table['fields']:
                        print(f"      - {field['name']} (typ: {field['type']})")
                
                SchemaPrinter.print_schema(schema)

                # Synchronizacja schematu
                print(f"\n5. Synchronizacja schematu bazy {base_name}...")
                sync_start_time = time.time()
                try:
                    schema_sync.sync_schema(base_id)
                except Exception as e:
                    print(f"!!! Błąd podczas synchronizacji schematu: {str(e)}")
                    print(f"Szczegóły błędu: {type(e).__name__}")
                    raise
                
                # Synchronizacja danych
                print(f"\n6. Synchronizacja danych bazy {base_name}...")
                try:
                    data_sync.sync_base_data(base_id)
                except Exception as e:
                    print(f"!!! Błąd podczas synchronizacji danych: {str(e)}")
                    print(f"Szczegóły błędu: {type(e).__name__}")
                    raise
                
                sync_time = time.time() - sync_start_time
                print(f"Czas synchronizacji bazy {base_name}: {sync_time:.2f} sekund")
                processed_bases += 1
                
            except Exception as e:
                print(f"!!! Błąd podczas przetwarzania bazy {base_name}: {str(e)}")
                print(f"Typ błędu: {type(e).__name__}")
                print(f"Szczegóły błędu: {e.__dict__ if hasattr(e, '__dict__') else 'Brak dodatkowych szczegółów'}")
                continue

        # Wyświetl listę tabel w PostgreSQL po synchronizacji
        print("\n=== Podsumowanie synchronizacji ===")
        print("\nTabele w PostgreSQL po synchronizacji:")
        postgres_tables = schema_sync.get_postgres_tables()
        for table in postgres_tables:
            print(f"- {table}")

        total_time = time.time() - start_time
        print("\n=== Podsumowanie końcowe ===")
        print(f"Całkowity czas wykonania: {total_time:.2f} sekund")
        print(f"Liczba przetworzonych baz: {processed_bases}/{len(bases)}")
        print(f"Liczba przetworzonych tabel: {total_tables}")
        print("Program zakończył działanie pomyślnie")

    except Exception as e:
        print(f"\n!!! Wystąpił krytyczny błąd: {e}")
        raise
    finally:
        if postgres_client:
            postgres_client.close()

if __name__ == "__main__":
    main()
