import pytest
from src.emsairtable.schema_sync import SchemaSync
from src.emsairtable.airtable_client import AirtableClient
from database.postgresql import PostgresClient


@pytest.fixture
def mock_airtable_client(mocker):
    client = mocker.Mock(spec=AirtableClient)
    return client


@pytest.fixture
def mock_postgres_client(mocker):
    client = mocker.Mock(spec=PostgresClient)
    client.schema = 'public'
    return client


@pytest.fixture
def schema_sync(mock_airtable_client, mock_postgres_client):
    return SchemaSync(mock_airtable_client, mock_postgres_client)


@pytest.fixture
def sample_airtable_schema():
    return {
        'name': 'Test Base',
        'id': 'base123',
        'tables': [
            {
                'name': 'Customers',
                'id': 'tbl123',
                'fields': [
                    {
                        'name': 'Name',
                        'type': 'singleLineText'
                    },
                    {
                        'name': 'Email',
                        'type': 'email'
                    },
                    {
                        'name': 'Age',
                        'type': 'number'
                    }
                ]
            }
        ]
    }


def test_get_postgres_tables(schema_sync, mock_postgres_client):
    """Test pobierania listy tabel z PostgreSQL."""
    mock_postgres_client.execute_query.return_value = [
        {'table_name': 'table1'},
        {'table_name': 'table2'}
    ]
    
    tables = schema_sync.get_postgres_tables()
    
    assert tables == ['table1', 'table2']
    mock_postgres_client.execute_query.assert_called_once()


def test_create_table(schema_sync, mock_postgres_client):
    """Test tworzenia nowej tabeli."""
    fields = [
        {'name': 'Name', 'type': 'singleLineText'},
        {'name': 'Email', 'type': 'email'},
        {'name': 'Age', 'type': 'number'}
    ]
    
    schema_sync.create_table('test_table', fields)
    
    # Sprawdź czy execute_modification został wywołany dwa razy
    # (raz dla CREATE TABLE i raz dla triggera)
    assert mock_postgres_client.execute_modification.call_count == 2
    
    # Sprawdź czy pierwsze wywołanie zawiera CREATE TABLE
    first_call = mock_postgres_client.execute_modification.call_args_list[0]
    create_sql = first_call[0][0].lower()
    
    # Sprawdzamy czy wszystkie wymagane elementy są w SQL-u
    required_elements = [
        'create table',
        'test_table',
        'id serial primary key',
        'airtable_id varchar(255)',
        'name varchar(255)',
        'email varchar(255)',
        'age numeric',
        'created_at timestamp',
        'updated_at timestamp'
    ]
    
    for element in required_elements:
        assert element in create_sql, f"Brak wymaganego elementu: {element}"

    # Sprawdzamy trigger
    trigger_sql = mock_postgres_client.execute_modification.call_args_list[1][0][0].lower()
    assert 'create trigger' in trigger_sql
    assert 'update_updated_at_trigger' in trigger_sql
    assert 'before update' in trigger_sql
    assert 'for each row' in trigger_sql


def test_sync_schema_new_table(schema_sync, mock_airtable_client, mock_postgres_client, sample_airtable_schema):
    """Test synchronizacji schematu gdy tabela nie istnieje."""
    mock_airtable_client.get_base_schema.return_value = sample_airtable_schema
    mock_postgres_client.execute_query.return_value = []  # Brak istniejących tabel
    
    schema_sync.sync_schema('base123')
    
    # Sprawdź czy pobrano schemat
    mock_airtable_client.get_base_schema.assert_called_once_with('base123')
    
    # Sprawdź czy sprawdzono istniejące tabele
    mock_postgres_client.execute_query.assert_called_once()
    
    # Sprawdź czy utworzono tabelę
    assert mock_postgres_client.execute_modification.call_count == 2
    create_sql = mock_postgres_client.execute_modification.call_args_list[0][0][0].lower()
    assert 'test_base_customers' in create_sql


def test_sync_schema_existing_table(schema_sync, mock_airtable_client, mock_postgres_client, sample_airtable_schema):
    """Test synchronizacji schematu gdy tabela już istnieje."""
    mock_airtable_client.get_base_schema.return_value = sample_airtable_schema
    mock_postgres_client.execute_query.return_value = [
        {'table_name': 'test_base_customers'}
    ]
    
    schema_sync.sync_schema('base123')
    
    # Sprawdź czy pobrano schemat
    mock_airtable_client.get_base_schema.assert_called_once_with('base123')
    
    # Sprawdź czy sprawdzono istniejące tabele
    mock_postgres_client.execute_query.assert_called_once()
    
    # Sprawdź czy NIE utworzono tabeli (bo już istnieje)
    assert mock_postgres_client.execute_modification.call_count == 0


def test_type_mapping(schema_sync):
    """Test mapowania typów danych."""
    assert schema_sync.type_mapping['singleLineText'] == 'VARCHAR(255)'
    assert schema_sync.type_mapping['multilineText'] == 'TEXT'
    assert schema_sync.type_mapping['number'] == 'NUMERIC'
    assert schema_sync.type_mapping['checkbox'] == 'BOOLEAN'
    assert schema_sync.type_mapping['date'] == 'DATE' 