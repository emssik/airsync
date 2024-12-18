import pytest
from src.emsairtable.schema_sync import SchemaSync
from src.emsairtable.airtable_client import AirtableClient
from src.database.postgresql import PostgresClient
from unittest.mock import Mock, patch


@pytest.fixture
def schema_sync():
    airtable_mock = Mock(spec=AirtableClient)
    postgres_mock = Mock(spec=PostgresClient)
    postgres_mock.schema = 'public'
    return SchemaSync(airtable_mock, postgres_mock)


def test_clean_name_basic(schema_sync):
    """Test podstawowego czyszczenia nazw."""
    assert schema_sync.clean_name("Test Field") == "test_field"
    assert schema_sync.clean_name("test.field") == "test_field"
    assert schema_sync.clean_name("test-field") == "test_field"
    assert schema_sync.clean_name("Test Field!@#") == "test_field"


def test_clean_name_numbers(schema_sync):
    """Test obsługi nazw zaczynających się od cyfr."""
    assert schema_sync.clean_name("1field") == "col_1field"
    assert schema_sync.clean_name("2.test") == "col_2_test"


def test_clean_name_special_chars(schema_sync):
    """Test obsługi specjalnych znaków."""
    assert schema_sync.clean_name("field.with.dots") == "field_with_dots"
    assert schema_sync.clean_name("field with spaces") == "field_with_spaces"
    assert schema_sync.clean_name("field-with-dashes") == "field_with_dashes"
    assert schema_sync.clean_name("field_with_underscore") == "field_with_underscore"


def test_create_table(schema_sync):
    """Test tworzenia tabeli z różnymi typami pól."""
    fields = [
        {"name": "Text Field", "type": "singleLineText"},
        {"name": "Number Field", "type": "number"},
        {"name": "Date Field", "type": "date"},
        {"name": "Record Link", "type": "multipleRecordLinks"},
        {"name": "checkbox.field", "type": "checkbox"},
    ]
    
    schema_sync.create_table("test_table", fields)
    
    expected_sql = """
        CREATE TABLE IF NOT EXISTS public.test_table (
            airtable_id TEXT PRIMARY KEY,
            text_field TEXT,
            number_field NUMERIC,
            date_field DATE,
            record_link TEXT,
            checkbox_field BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    schema_sync.postgres.execute_modification.assert_called()
    actual_sql = schema_sync.postgres.execute_modification.call_args_list[0][0][0]
    assert ' '.join(actual_sql.split()) == ' '.join(expected_sql.split())


def test_type_mapping(schema_sync):
    """Test mapowania typów Airtable na typy PostgreSQL."""
    assert schema_sync.type_mapping["singleLineText"] == "TEXT"
    assert schema_sync.type_mapping["multilineText"] == "TEXT"
    assert schema_sync.type_mapping["number"] == "NUMERIC"
    assert schema_sync.type_mapping["checkbox"] == "BOOLEAN"
    assert schema_sync.type_mapping["date"] == "DATE"
    assert schema_sync.type_mapping["multipleRecordLinks"] == "TEXT"
    assert schema_sync.type_mapping["formula"] == "TEXT"


def test_sync_schema(schema_sync):
    """Test synchronizacji schematu bazy."""
    schema_sync.airtable.get_base_schema.return_value = {
        "name": "Test Base",
        "tables": [
            {
                "name": "Test Table",
                "fields": [
                    {"name": "Field 1", "type": "singleLineText"},
                    {"name": "Field.2", "type": "number"},
                ]
            }
        ]
    }
    
    schema_sync.get_postgres_tables = Mock(return_value=[])
    schema_sync.create_table = Mock()
    
    schema_sync.sync_schema("base_id")
    
    schema_sync.create_table.assert_called_once()
    table_name, fields = schema_sync.create_table.call_args[0]
    assert table_name == "test_base_test_table"
    assert len(fields) == 2 