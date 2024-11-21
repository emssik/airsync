from dotenv import load_dotenv
import os
import time
from emsairtable.airtable_client import AirtableClient
from emsairtable.schema_printer import SchemaPrinter

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Odczytaj klucz API
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def main():
    """Główna funkcja programu eksportująca wszystkie dostępne bazy Airtable do CSV"""
    if not AIRTABLE_API_KEY:
        print("Błąd: Brak klucza API Airtable")
        return

    try:
        print("=== Start programu ===")
        start_time = time.time()
        
        # Inicjalizacja klienta Airtable
        print("\n1. Inicjalizacja połączenia z Airtable...")
        client = AirtableClient(AIRTABLE_API_KEY)
        
        # Pobierz wszystkie bazy
        print("\n2. Pobieranie listy baz...")
        bases = client.list_bases()
        bases_time = time.time()
        print(f"Znaleziono {len(bases)} baz danych:")
        for base_id, base_name in bases.items():
            print(f"- {base_name} (ID: {base_id})")
        print(f"Czas pobierania listy baz: {bases_time - start_time:.2f} sekund")

        # Utwórz katalog exports jeśli nie istnieje
        output_dir = "exports"
        if not os.path.exists(output_dir):
            print(f"\nTworzenie katalogu {output_dir}...")
            os.makedirs(output_dir)

        total_exported_files = []
        total_tables = 0
        
        # Iteruj przez wszystkie bazy
        for base_id, base_name in bases.items():
            print(f"\n=== Przetwarzanie bazy: {base_name} ===")
            
            # Pobierz schemat bazy
            print(f"3. Pobieranie schematu bazy {base_name}...")
            try:
                schema = client.get_base_schema(base_id)
                print(f"Znaleziono {len(schema['tables'])} tabel w bazie")
                total_tables += len(schema['tables'])
                
                print("\n4. Szczegółowy schemat bazy:")
                SchemaPrinter.print_schema(schema)

                # Eksport tabel do CSV
                print(f"\n5. Rozpoczynam eksport tabel z bazy {base_name}...")
                export_start_time = time.time()
                
                # Eksportuj tabele i mierz czas dla każdej z nich
                exported_files = client.export_tables_to_csv(base_id, output_dir)
                total_exported_files.extend(exported_files)
                
                export_time = time.time() - export_start_time
                print(f"Czas eksportu bazy {base_name}: {export_time:.2f} sekund")
                
            except Exception as e:
                print(f"!!! Błąd podczas przetwarzania bazy {base_name}: {e}")
                continue

        # Podsumowanie całego eksportu
        if total_exported_files:
            print("\n=== Podsumowanie eksportu ===")
            total_size = 0
            print("\nWyeksportowane pliki:")
            for filepath in total_exported_files:
                file_size = os.path.getsize(filepath) / 1024  # rozmiar w KB
                total_size += file_size
                print(f"- {os.path.basename(filepath)} ({file_size:.2f} KB)")
            print(f"\nŁączny rozmiar wyeksportowanych plików: {total_size:.2f} KB")
        else:
            print("\nNie wyeksportowano żadnych plików")

        total_time = time.time() - start_time
        print("\n=== Podsumowanie końcowe ===")
        print(f"Całkowity czas wykonania: {total_time:.2f} sekund")
        print(f"Liczba przetworzonych baz: {len(bases)}")
        print(f"Liczba przetworzonych tabel: {total_tables}")
        print(f"Liczba wyeksportowanych plików: {len(total_exported_files)}")
        print("Program zakończył działanie pomyślnie")

    except Exception as e:
        print(f"\n!!! Wystąpił błąd: {e}")
        raise

if __name__ == "__main__":
    main()
