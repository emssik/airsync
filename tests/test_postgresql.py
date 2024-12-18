import os
import pytest
import yaml
from dotenv import load_dotenv
from database.postgresql import PostgresClient

@pytest.fixture
def db_config():
    """Wczytuje konfigurację bazy danych z pliku config.yaml"""
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config['database']

@pytest.fixture
def db_client(db_config):
    """Tworzy instancję PostgresClient z konfiguracją"""
    load_dotenv()  # Wczytuje zmienne środowiskowe z .env
    
    # Dodaje hasło z zmiennej środowiskowej do konfiguracji
    db_config['password'] = os.getenv('POSTGRESQL_PASSWORD')
    
    client = PostgresClient(db_config)
    yield client
    client.close()  # Zamyka połączenie po zakończeniu testu

def test_database_connection(db_client):
    """Sprawdza, czy połączenie z bazą danych działa"""
    try:
        # Proste zapytanie testowe
        result = db_client.execute_query("SELECT 1 as test")
        assert len(result) == 1
        assert result[0]['test'] == 1
    except Exception as e:
        pytest.fail(f"Nie udało się połączyć z bazą danych: {str(e)}") 