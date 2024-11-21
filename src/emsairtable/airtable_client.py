from typing import Dict, Optional
from pyairtable import Api
from pyairtable.api.table import Table


class AirtableClient:
    def __init__(self, api_key: str):
        """
        Inicjalizuje klienta Airtable.
        
        Args:
            api_key: Klucz API do Airtable
        """
        self._api = Api(api_key)

    def get_base_schema(self, base_id: str) -> Dict:
        """
        Pobiera szczegółowy schemat bazy danych Airtable.
        
        Args:
            base_id: ID bazy Airtable
            
        Returns:
            Dict zawierający strukturę bazy z informacjami o tabelach i polach
        """
        base = self._api.base(base_id)
        schema = base.schema()
        
        return {
            'name': base.name,
            'id': base.id,
            'tables': [{
                'name': table.name,
                'id': table.id,
                'fields': [{
                    'name': field.name,
                    'type': field.type,
                    'options': getattr(field, 'options', {}) or {}
                } for field in table.fields]
            } for table in schema.tables]
        }

    def list_bases(self) -> Dict[str, str]:
        """
        Zwraca słownik z ID i nazwami wszystkich baz.
        
        Returns:
            Dict[str, str]: Słownik {base_id: base_name}
        """
        bases = self._api.bases()
        return {base.id: base.name for base in bases}

    def get_table(self, base_id: str, table_name: str) -> Optional[Table]:
        """
        Zwraca obiekt tabeli o podanej nazwie z określonej bazy.
        
        Args:
            base_id: ID bazy
            table_name: Nazwa tabeli
            
        Returns:
            Optional[Table]: Obiekt tabeli lub None jeśli nie znaleziono
        """
        base = self._api.base(base_id)
        try:
            return base.table(table_name)
        except KeyError:
            return None
