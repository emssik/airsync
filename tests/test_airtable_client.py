import pytest
from unittest.mock import Mock, patch
from src.emsairtable.airtable_client import AirtableClient

@pytest.fixture
def mock_api():
    with patch('src.emsairtable.airtable_client.Api') as mock:
        yield mock

def test_initialization(mock_api):
    """Test inicjalizacji klienta Airtable."""
    with patch('src.emsairtable.airtable_client.Api') as mock:
        client = AirtableClient("fake_api_key")
        mock.assert_called_once_with("fake_api_key")

def test_get_base_schema(mock_api):
    """Test pobierania schematu bazy."""
    # Przygotuj mocki pól z konkretnymi wartościami
    mock_field1 = Mock()
    mock_field1.name = "Field 1"
    mock_field1.type = "singleLineText"
    
    mock_field2 = Mock()
    mock_field2.name = "Field 2"
    mock_field2.type = "number"
    
    # Przygotuj mock tabeli
    mock_table = Mock()
    mock_table.name = "Table 1"
    mock_table.fields = [mock_field1, mock_field2]
    
    mock_schema = Mock()
    mock_schema.tables = [mock_table]
    
    # Skonfiguruj mock API
    mock_base = Mock()
    mock_base.schema = Mock(return_value=mock_schema)
    mock_api.return_value.base = Mock(return_value=mock_base)

    with patch('src.emsairtable.airtable_client.Api') as mock:
        mock.return_value.base = Mock(return_value=mock_base)
        client = AirtableClient("fake_api_key")
        schema = client.get_base_schema("base_id")

        # Sprawdź, czy schema ma oczekiwaną strukturę
        assert "name" in schema
        assert "tables" in schema
        assert len(schema["tables"]) == 1
        assert schema["tables"][0]["name"] == "Table 1"
        assert len(schema["tables"][0]["fields"]) == 2
        assert schema["tables"][0]["fields"][0]["name"] == "Field 1"
        assert schema["tables"][0]["fields"][0]["type"] == "singleLineText"
        assert schema["tables"][0]["fields"][1]["name"] == "Field 2"
        assert schema["tables"][0]["fields"][1]["type"] == "number"

def test_get_table_records(mock_api):
    """Test pobierania rekordów z tabeli."""
    expected_records = [
        {"id": "rec1", "fields": {"Field 1": "Value 1"}},
        {"id": "rec2", "fields": {"Field 1": "Value 2"}}
    ]
    
    # Przygotuj mock dla table
    mock_table = Mock()
    mock_table.all.return_value = expected_records

    # Skonfiguruj mock dla Api().table(base_id, table_name)
    mock_api.return_value.table = Mock(return_value=mock_table)

    # Wykonaj test
    client = AirtableClient("fake_api_key")
    actual_records = client.get_table_records("base_id", "table_name")

    # Sprawdź wynik
    assert actual_records == expected_records
  