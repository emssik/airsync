from dotenv import load_dotenv
import os
from pyairtable import Api

# Załaduj zmienne środowiskowe z pliku .env
load_dotenv()

# Odczytaj klucz API
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')

def get_all_bases():
    """Pobiera listę wszystkich dostępnych baz z Airtable"""
    try:
        api = Api(AIRTABLE_API_KEY)
        bases = api.bases()
        return bases
    except Exception as e:
        print(f"Wystąpił błąd podczas pobierania baz: {e}")
        return None

if __name__ == "__main__":
    print(f"Klucz API został załadowany: {'tak' if AIRTABLE_API_KEY else 'nie'}")
    
    bases = get_all_bases()
    if bases:
        print("\nDostępne bazy:")
        for base in bases:
            print(f"- {base.name} (ID: {base.id})")
