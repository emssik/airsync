import os
from pathlib import Path
import yaml
from dotenv import load_dotenv


def load_config():
    """Wczytuje config.yaml względem katalogu src/."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def build_pg_config(config: dict) -> dict:
    """Buduje słownik konfiguracji PostgreSQL z configa i zmiennych środowiskowych."""
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
    return pg_config
