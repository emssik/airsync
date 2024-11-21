import pytest
from unittest.mock import Mock, patch
from src.emsairtable.airtable_client import AirtableClient

@pytest.fixture
def mock_api():
    with patch('src.emsairtable.airtable_client.Api') as mock_api:
        # Przygotuj mocki dla baz
        base1 = Mock()
        base1.id = "base1"
        base1.name = "Test Base 1"
        
        base2 = Mock()
        base2.id = "base2"
        base2.name = "Test Base 2"
        
        # Przygotuj mocki dla tabel
        table1 = Mock()
        table1.id = "tbl1"
        table1.name = "Table 1"
        
        table2 = Mock()
        table2.id = "tbl2"
        table2.name = "Table 2"
        
        # Dodaj mock dla schema() w table1
        table1.schema.return_value = {
            'fields': [
                {
                    'name': 'Name',
                    'type': 'singleLineText',
                    'options': {'precision': 2}
                },
                {
                    'name': 'Age',
                    'type': 'number',
                    'typeOptions': {'format': 'integer'}
                },
                {
                    'name': 'Status',
                    'type': 'multipleSelect',
                    'options': {'choices': ['Active', 'Inactive']}
                }
            ]
        }
        
        # Skonfiguruj zachowanie mocków
        base1.tables.return_value = [table1]
        base2.tables.return_value = [table2]
        mock_api.return_value.bases.return_value = [base1, base2]
        
        yield mock_api.return_value

def test_initialization(mock_api):
    client = AirtableClient("fake_api_key")
    assert mock_api.bases.called
    assert len(client.list_bases()) == 2

def test_refresh_metadata(mock_api):
    client = AirtableClient("fake_api_key")
    client.refresh_metadata()
    assert mock_api.bases.call_count == 2

def test_get_base(mock_api):
    client = AirtableClient("fake_api_key")
    base = client.get_base("base1")
    assert base is not None
    assert base.id == "base1"

def test_get_nonexistent_base(mock_api):
    client = AirtableClient("fake_api_key")
    base = client.get_base("nonexistent")
    assert base is None

def test_list_bases(mock_api):
    client = AirtableClient("fake_api_key")
    bases = client.list_bases()
    assert len(bases) == 2
    assert bases["base1"] == "Test Base 1"
    assert bases["base2"] == "Test Base 2"

def test_list_tables(mock_api):
    client = AirtableClient("fake_api_key")
    tables = client.list_tables("base1")
    assert len(tables) == 1
    assert "Table 1" in tables 

def test_get_base_schema(mock_api):
    client = AirtableClient("fake_api_key")
    schema = client.get_base_schema("base1")
    
    # Sprawdź podstawowe informacje o bazie
    assert schema['name'] == "Test Base 1"
    assert schema['id'] == "base1"
    assert len(schema['tables']) == 1
    
    # Sprawdź informacje o tabeli
    table = schema['tables'][0]
    assert table['name'] == "Table 1"
    assert table['id'] == "tbl1"
    assert len(table['fields']) == 3
    
    # Sprawdź pola
    fields = table['fields']
    assert fields[0]['name'] == "Name"
    assert fields[0]['type'] == "singleLineText"
    assert fields[0]['options'] == {'precision': 2}
    
    assert fields[1]['name'] == "Age"
    assert fields[1]['type'] == "number"
    assert fields[1]['options'] == {'format': 'integer'}
    
    assert fields[2]['name'] == "Status"
    assert fields[2]['type'] == "multipleSelect"
    assert fields[2]['options'] == {'choices': ['Active', 'Inactive']}

def test_get_base_schema_nonexistent_base(mock_api):
    client = AirtableClient("fake_api_key")
    with pytest.raises(ValueError, match="Nie znaleziono bazy o ID: nonexistent"):
        client.get_base_schema("nonexistent")

def test_get_base_schema_empty_table(mock_api):
    # Modyfikujemy mock dla table1, aby zwracał pustą listę pól
    for base in mock_api.bases.return_value:
        if base.id == "base1":
            base.tables.return_value[0].schema.return_value = {'fields': []}
    
    client = AirtableClient("fake_api_key")
    schema = client.get_base_schema("base1")
    
    assert len(schema['tables']) == 1
    assert len(schema['tables'][0]['fields']) == 0
  