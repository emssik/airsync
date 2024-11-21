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
        self._bases = self._api.bases()

    def get_base_schema(self, base_id: str) -> Dict:
        """
        Pobiera szczegółowy schemat bazy danych Airtable.
        
        Args:
            base_id: ID bazy Airtable
            
        Returns:
            Dict zawierający strukturę bazy z informacjami o tabelach i polach
        
        Raises:
            ValueError: Gdy nie znaleziono bazy o podanym ID
        """
        base = self.get_base(base_id)
        if not base:
            raise ValueError(f"Nie znaleziono bazy o ID: {base_id}")
        
        # Pobieramy cały schemat bazy
        base_schema = base.schema()
        
        result = {
            'name': base.name,
            'id': base.id,
            'tables': []
        }
        
        # Iterujemy po tabelach w schemacie
        for table in base_schema.tables:
            table_info = {
                'name': table.name,
                'id': table.id,
                'fields': []
            }
            
            # Dodajemy informacje o polach tylko jeśli istnieją
            if hasattr(table, 'fields') and table.fields:
                for field in table.fields:
                    field_info = {
                        'name': field.name,
                        'type': field.type,
                        'options': {}
                    }
                    
                    # Dodajemy opcje pola jeśli istnieją
                    if hasattr(field, 'options') and field.options:
                        field_info['options'] = field.options
                    
                    table_info['fields'].append(field_info)
                
            result['tables'].append(table_info)
        
        return result

    def list_bases(self) -> Dict[str, str]:
        """
        Zwraca słownik z ID i nazwami wszystkich baz.
        
        Returns:
            Dict[str, str]: Słownik {base_id: base_name}
        """
        return {base.id: base.name for base in self._bases}

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

    def refresh_metadata(self):
        """
        Odświeża metadane baz danych.
        """
        self._bases = self._api.bases()

    def get_base(self, base_id: str):
        """
        Zwraca obiekt bazy o podanym ID.
        
        Args:
            base_id: ID bazy Airtable
            
        Returns:
            Obiekt bazy lub None jeśli nie znaleziono
        """
        for base in self._bases:
            if base.id == base_id:
                return base
        return None

    def list_tables(self, base_id: str) -> list[str]:
        """
        Zwraca listę nazw tabel dla podanej bazy.
        
        Args:
            base_id: ID bazy Airtable
            
        Returns:
            list[str]: Lista nazw tabel
        """
        base = self.get_base(base_id)
        if base:
            tables = base.tables()
            return [table.name for table in tables]
        return []
