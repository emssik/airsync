from typing import Dict, List
from pyairtable import Api
from pyairtable.formulas import match


class AirtableClient:
    def __init__(self, api_key: str):
        """
        Inicjalizuje klienta Airtable.
        
        Args:
            api_key: Klucz API lub token dostępu do Airtable
        """
        self.api = Api(api_key)

    def get_base_schema(self, base_id: str) -> Dict:
        """
        Pobiera schemat bazy Airtable.
        
        Args:
            base_id: ID bazy Airtable
        Returns:
            Schemat bazy zawierający informacje o tabelach i polach
        """
        base = self.api.base(base_id)
        schema = base.schema()
        
        # Pobierz nazwę bazy z listy baz
        bases = self.list_bases()
        base_name = bases.get(base_id, base_id).lower().replace(' ', '_')
        
        return {
            'id': base_id,
            'name': base_name,
            'tables': [{
                'id': table.id,
                'name': table.name,
                'pg_name': f"{base_name}_{table.name.lower().replace(' ', '_')}",
                'fields': [{
                    'id': field.id,
                    'name': field.name,
                    'type': self._normalize_field_type(field.type),
                    'options': field.options if hasattr(field, 'options') else None
                } for field in table.fields]
            } for table in schema.tables]
        }

    def _normalize_field_type(self, airtable_type: str) -> str:
        """
        Normalizuje typ pola z Airtable do standardowego formatu.
        
        Args:
            airtable_type: Oryginalny typ pola z Airtable
        Returns:
            Znormalizowany typ pola
        """
        type_mapping = {
            'multipleAttachments': 'text',
            'multilineText': 'multilineText',
            'singleLineText': 'singleLineText',
            'checkbox': 'checkbox',
            'date': 'date',
            'dateTime': 'dateTime',
            'number': 'number',
            'currency': 'currency',
            'percent': 'number',
            'email': 'email',
            'url': 'url',
            'phoneNumber': 'phone',
            'multipleSelects': 'multipleSelects',
            'singleSelect': 'singleSelect',
            'multipleRecordLinks': 'multipleRecordLinks',
            'formula': 'formula',
            'rollup': 'text',
            'count': 'count',
            'lookup': 'text'
        }
        return type_mapping.get(airtable_type, 'text')

    def get_table_records(self, base_id: str, table_name: str) -> List[Dict]:
        """
        Pobiera wszystkie rekordy z tabeli Airtable.
        
        Args:
            base_id: ID bazy Airtable
            table_name: Nazwa tabeli
        Returns:
            Lista rekordów z tabeli
        """
        table = self.api.table(base_id, table_name)
        return table.all()

    def get_table_record(self, base_id: str, table_name: str, record_id: str) -> Dict:
        """
        Pobiera pojedynczy rekord z tabeli Airtable.
        
        Args:
            base_id: ID bazy Airtable
            table_name: Nazwa tabeli
            record_id: ID rekordu
        Returns:
            Rekord z tabeli
        """
        table = self.api.table(base_id, table_name)
        return table.get(record_id)

    def find_records(self, base_id: str, table_name: str, filter_by: Dict = None) -> List[Dict]:
        """
        Wyszukuje rekordy w tabeli Airtable spełniające określone kryteria.
        
        Args:
            base_id: ID bazy Airtable
            table_name: Nazwa tabeli
            filter_by: Słownik z kryteriami wyszukiwania {nazwa_pola: wartość}
        Returns:
            Lista znalezionych rekordów
        """
        table = self.api.table(base_id, table_name)
        if filter_by:
            formula = match(filter_by)
            return table.all(formula=formula)
        return table.all()

    def list_bases(self) -> Dict[str, str]:
        """
        Pobiera listę wszystkich dostępnych baz danych.
        
        Returns:
            Dict[str, str]: Słownik z ID bazy jako kluczem i nazwą bazy jako wartością
        """
        bases = self.api.bases()
        return {base.id: base.name for base in bases}
