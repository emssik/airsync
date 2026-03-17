from dotenv import load_dotenv
import os
import time
import argparse
from emsairtable.airtable_client import AirtableClient
from emsairtable.schema_sync import SchemaSync
from emsairtable.data_sync import DataSync
from database.postgresql import PostgresClient
from config import load_config, build_pg_config

def main():
    """Główna funkcja programu synchronizująca wszystkie dostępne bazy Airtable z PostgreSQL"""
    parser = argparse.ArgumentParser(description='Synchronizacja Airtable do PostgreSQL')
    parser.add_argument('--base-id', help='ID konkretnej bazy Airtable do synchronizacji (domyślnie: wszystkie)')
    parser.add_argument('--dry-run', action='store_true', help='Pobierz dane z Airtable i pokaż co zostałoby zrobione, bez zapisu do bazy')
    args = parser.parse_args()

    # Wczytaj zmienne środowiskowe i konfigurację
    load_dotenv()
    config = load_config()

    # Konfiguracja Airtable
    AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

    if not AIRTABLE_API_KEY:
        print("Błąd: Brak klucza API Airtable")
        return

    if args.dry_run:
        pg_config = {'schema': config['database'].get('schema', os.getenv('POSTGRES_SCHEMA', 'public'))}
    else:
        pg_config = build_pg_config(config)

    # Pobierz listę wykluczonych baz
    excluded_databases = config['database'].get('excluded_databases', [])

    postgres_client = None
    try:
        if args.dry_run:
            print("=== Start programu (DRY RUN — bez zapisu do bazy) ===")
        else:
            print("=== Start programu ===")
        start_time = time.time()

        # Inicjalizacja klientów
        print("\nInicjalizacja połączenia z Airtable i PostgreSQL...")
        airtable_client = AirtableClient(AIRTABLE_API_KEY)
        postgres_client = PostgresClient(pg_config, dry_run=args.dry_run)

        # Inicjalizacja synchronizatorów
        schema_sync = SchemaSync(airtable_client, postgres_client)
        data_sync = DataSync(airtable_client, postgres_client, schema_sync=schema_sync)

        # Pobierz wszystkie bazy
        print("\nPobieranie listy baz...")
        bases = airtable_client.list_bases()
        bases_time = time.time()
        print(f"Znaleziono {len(bases)} baz danych:")
        for base_id, base_name in bases.items():
            print(f"- {base_name} (ID: {base_id})")
        print(f"Czas pobierania listy baz: {bases_time - start_time:.2f} sekund")

        # Jeśli podano --base-id, synchronizuj tylko tę bazę
        if args.base_id:
            if args.base_id not in bases:
                print(f"Błąd: Nie znaleziono bazy o ID {args.base_id}")
                return
            bases = {args.base_id: bases[args.base_id]}

        total_tables = 0
        processed_bases = 0
        failed_bases = []  # Lista nieudanych synchronizacji

        # Iteruj przez wszystkie bazy
        for base_id, base_name in bases.items():
            # Sprawdź czy baza nie jest wykluczona
            if base_name in excluded_databases:
                print(f"\n=== Pomijanie wykluczonej bazy: {base_name} ===")
                continue

            print(f"\n=== Przetwarzanie bazy: {base_name} ===")
            print(f"ID bazy: {base_id}")

            try:
                # Pobierz schemat bazy
                print(f"Pobieranie schematu bazy {base_name}...")
                schema = airtable_client.get_base_schema(base_id)
                print(f"Znaleziono {len(schema['tables'])} tabel w bazie")
                total_tables += len(schema['tables'])

                # Synchronizacja schematu
                print(f"Synchronizacja schematu bazy {base_name}...")
                sync_start_time = time.time()
                try:
                    schema_sync.sync_schema(base_id, base_schema=schema)
                except Exception as e:
                    print(f"!!! Błąd podczas synchronizacji schematu: {str(e)}")
                    print(f"Szczegóły błędu: {type(e).__name__}")
                    raise

                # Synchronizacja danych
                print(f"Synchronizacja danych bazy {base_name}...")
                try:
                    data_sync.sync_base_data(base_id, base_schema=schema)
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
                failed_bases.append((base_name, str(e)))
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

        if failed_bases:
            print("\n=== Bazy, których nie udało się zsynchronizować ===")
            for base_name, error in failed_bases:
                print(f"- {base_name}: {error}")

        print("Program zakończył działanie pomyślnie")

    except Exception as e:
        print(f"\n!!! Wystąpił krytyczny błąd: {e}")
        raise
    finally:
        if postgres_client:
            postgres_client.close()

if __name__ == "__main__":
    main()
