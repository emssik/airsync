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
    """Główna funkcja programu wyświetlająca informacje o bazie Mentoring"""
    if not AIRTABLE_API_KEY:
        print("Błąd: Brak klucza API Airtable")
        return

    try:
        start_time = time.time()
        
        # Inicjalizacja klienta Airtable
        client = AirtableClient(AIRTABLE_API_KEY)
        
        # Pobierz wszystkie bazy
        print("Pobieranie listy baz...")
        bases = client.list_bases()
        bases_time = time.time()
        print(f"Czas pobierania listy baz: {bases_time - start_time:.2f} sekund")
        
        # Znajdź bazę Mentoring
        mentoring_base_id = None
        for base_id, base_name in bases.items():
            if base_name == "Mentoring":
                mentoring_base_id = base_id
                break
        
        if not mentoring_base_id:
            print("Nie znaleziono bazy 'Mentoring'")
            return
            
        # Pobierz i wyświetl szczegółowy schemat bazy Mentoring
        print("\nPobieranie schematu bazy Mentoring...")
        schema = client.get_base_schema(mentoring_base_id)
        schema_time = time.time()
        print(f"Czas pobierania schematu: {schema_time - bases_time:.2f} sekund")
        
        print("\nSzczegółowy schemat bazy Mentoring:")
        SchemaPrinter.print_schema(schema)
        
        total_time = time.time() - start_time
        print(f"\nCałkowity czas wykonania: {total_time:.2f} sekund")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    main()
