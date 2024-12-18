from typing import Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


class PostgresClient:
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Inicjalizacja klienta PostgreSQL.
        
        Args:
            connection_params: Słownik z parametrami połączenia
        """
        self.host = connection_params['host']
        self.port = connection_params['port']
        self.dbname = connection_params['database_name']
        self.user = connection_params['user']
        self.password = connection_params.get('password')
        self.schema = connection_params.get('schema', 'public')
        
        self._conn = None

    @contextmanager
    def get_connection(self):
        """Context manager do zarządzania połączeniem."""
        if self._conn is None:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password
            )
        try:
            yield self._conn
        except Exception as e:
            self._conn.rollback()
            raise e

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """Context manager do zarządzania kursorem."""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            finally:
                cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Wykonuje zapytanie SELECT i zwraca wyniki.
        
        Args:
            query: Zapytanie SQL
            params: Parametry do zapytania
            
        Returns:
            Lista wyników zapytania
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_modification(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Wykonuje zapytanie modyfikujące dane (INSERT, UPDATE, DELETE).
        
        Args:
            query: Zapytanie SQL
            params: Parametry do zapytania
            
        Returns:
            Liczba zmodyfikowanych wierszy
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def close(self):
        """Zamyka połączenie z bazą danych."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None 