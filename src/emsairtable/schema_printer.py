import json
from typing import Dict

class SchemaPrinter:
    """Klasa odpowiedzialna za formatowanie i wyświetlanie schematów Airtable."""
    
    @staticmethod
    def serialize_options(obj) -> Dict:
        """
        Pomocnicza metoda do serializacji obiektów opcji pól Airtable.
        
        Args:
            obj: Obiekt do serializacji
            
        Returns:
            Dict lub str reprezentujące opcje pola
        """
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return str(obj)

    @classmethod
    def print_schema(cls, schema: Dict, indent: int = 0) -> None:
        """
        Wyświetla schemat bazy w czytelnym formacie.

        Args:
            schema: Słownik zawierający schemat bazy
            indent: Poziom wcięcia (domyślnie 0)
        """
        print(cls.get_schema_str(schema, indent))

    @classmethod
    def get_schema_str(cls, schema: Dict, indent: int = 0) -> str:
        """
        Zwraca schemat bazy jako sformatowany tekst.
        
        Args:
            schema: Słownik zawierający schemat bazy
            indent: Poziom wcięcia (domyślnie 0)
            
        Returns:
            str: Sformatowany tekst reprezentujący schemat
        """
        lines = []
        prefix = "  " * indent
        
        lines.append(f"{prefix}Nazwa bazy: {schema['name']}")
        lines.append(f"{prefix}ID bazy: {schema['id']}")
        lines.append(f"{prefix}Tabele:")
        
        for table in schema['tables']:
            lines.append(f"{prefix}  - Tabela: {table['name']}")
            lines.append(f"{prefix}    ID: {table['id']}")
            lines.append(f"{prefix}    Pola:")
            
            for field in table['fields']:
                lines.append(f"{prefix}      - {field['name']} (typ: {field['type']})")
                if field['options']:
                    try:
                        options_str = json.dumps(
                            cls.serialize_options(field['options']), 
                            indent=2, 
                            ensure_ascii=False
                        )
                        lines.append(f"{prefix}        Opcje: {options_str}")
                    except Exception:
                        lines.append(f"{prefix}        Opcje: {field['options']}")
        
        return "\n".join(lines) 