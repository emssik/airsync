# Changelog

Wszystkie istotne zmiany w tym projekcie są dokumentowane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
projekt stosuje [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0] - 2026-03-17

### Added
- Skrypt `deploy.sh` — automatyzacja lokalnego buildu, szyfrowania sekretów (SOPS/age) i deploymentu na serwer via SSH
- Skrypt `deploy-server.sh` — po stronie serwera: deszyfrowanie sekretów i restart kontenerów via Docker Compose
- `compose.prod.yaml` — konfiguracja produkcyjna Docker Compose z obrazem z GHCR i healthcheckiem bazy danych
- `.dockerignore` — wykluczenie plików wrażliwych i zbędnych z kontekstu Docker build
- `secrets.enc.env` — zaszyfrowane sekrety środowiskowe (SOPS/age); bezpieczne do przechowywania w repozytorium
- `specs/problems.md` — code review identyfikujący krytyczne bugi, naruszenia DRY/KISS i priorytety napraw

## [0.2.0] - 2026-03-11

### Added
- Tryb `--dry-run` — podgląd synchronizacji bez zapisu do bazy danych
- Parametr `--base-id` — synchronizacja wybranej bazy Airtable po ID zamiast wszystkich
- Moduł `src/config.py` z funkcjami `load_config()` i `build_pg_config()` wydzielonymi z `main.py`
- Metoda `PostgresClient.execute_many()` do wsadowego zapisu rekordów (`executemany`)
- Metoda `SchemaSync.resolve_columns()` — deterministyczna deduplikacja nazw kolumn, spójna między `create_table` a upsert
- Rozbudowana lista zarezerwowanych słów PostgreSQL w `schema_sync.py`

### Changed
- Schemat bazy danych pobierany jednorazowo i przekazywany w dół — eliminacja zbędnych wywołań API Airtable
- `DataSync` przyjmuje opcjonalną instancję `SchemaSync` (dependency injection zamiast tworzenia wewnętrznego)
- `AirtableClient._normalize_field_type()` zwraca teraz surowy typ Airtable; całe mapowanie na typy SQL przeniesione do `SchemaSync`
- `SchemaPrinter.print_schema()` deleguje do `get_schema_str()` — usunięta zduplikowana logika formatowania
- Host bazy danych zmieniony z hardkodowanego IP na nazwę serwisu Docker (`airsync-db`)
- Poetry zaktualizowane do wersji 1.8.5 w Dockerfile; poprawiona ścieżka `COPY` w obrazie
- Ścieżka do `config.yaml` rozwiązywana względem pliku `config.py`, nie katalogu roboczego
- Uproszczony i oczyszczony output `main.py` — usunięto numerowane kroki i zbędne wypisywanie schematów
- `pyproject.toml`: dodano `package-mode = false`

### Fixed
- **Krytyczne**: Podatność SQL Injection — nazwy tabel i kolumn otoczone `psycopg2.sql.Identifier()` w całym kodzie
- **Krytyczne**: Niespójność kolumn między `create_table` a upsert prowadząca do zapisu danych w złe kolumny
- `_batch_upsert_records` używa teraz faktycznego wsadu (`execute_many`) zamiast pętli z osobnymi insertami
- `get_connection` sprawdza stan połączenia (`conn.closed`) przed próbą reużycia
- `PostgresClient` nie wymaga parametrów połączenia w trybie dry-run

### Removed
- `sync_mentoring_schema.py` — zastąpiony parametrem `--base-id` w `main.py`
- Podwójne mapowanie typów z `AirtableClient._normalize_field_type()`

## [0.1.0] - 2025-01-01

### Added
- Pierwsza wersja synchronizatora Airtable → PostgreSQL
