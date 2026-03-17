# airsync

> This project is published as part of [PIY — Prompt It Yourself](https://blog.atdpath.com/piy), a personal initiative launched on March 8, 2026, encouraging others to build their own apps with the help of LLMs.

Narzędzie do automatycznej synchronizacji baz Airtable do PostgreSQL. Pobiera schematy i dane ze wszystkich dostępnych baz Airtable, tworzy odpowiadające im tabele w PostgreSQL i utrzymuje dane w synchronizacji.

## Funkcje

- Synchronizacja wielu baz Airtable jednocześnie
- Automatyczne tworzenie tabel PostgreSQL na podstawie schematów Airtable
- UPSERT — wstawia nowe rekordy lub aktualizuje istniejące
- Mapowanie typów Airtable na typy PostgreSQL
- Automatyczne kolumny `created_at` i `updated_at`
- Tryb dry-run — podgląd zmian bez zapisu do bazy
- Synchronizacja wybranej bazy po ID
- Lista wykluczeń w konfiguracji
- Harmonogram cron (codziennie o 2:00)

## Wymagania

- Python 3.12+
- Poetry
- PostgreSQL 17
- Docker i Docker Compose (do deployu)

## Zmienne środowiskowe

| Zmienna | Opis |
|---|---|
| `AIRTABLE_API_KEY` | Klucz API do Airtable |
| `POSTGRESQL_PASSWORD` | Hasło do bazy PostgreSQL |
| `POSTGRES_SCHEMA` | Schemat PostgreSQL (domyślnie `public`) |

## Instalacja lokalna

```bash
poetry install
```

## Konfiguracja

Skopiuj pliki przykładowe i uzupełnij własnymi danymi:

```bash
cp .env.example .env
cp config.yaml.example config.yaml
```

- `.env` — klucz API Airtable i hasło do PostgreSQL
- `config.yaml` — adres bazy danych, użytkownik i lista wykluczonych baz Airtable

## Uruchomienie

```bash
# Synchronizacja wszystkich baz
poetry run python src/main.py

# Synchronizacja konkretnej bazy
poetry run python src/main.py --base-id APP123

# Podgląd bez zapisu (dry-run)
poetry run python src/main.py --dry-run
```

## Docker

### Budowanie obrazów

```bash
./docker/build.sh
```

### Deploy produkcyjny

```bash
docker compose -f compose.prod.yaml up -d
```

## Stack technologiczny

- **pyairtable 2.3.6** — klient API Airtable (wersja 3.0.0 nie działa zgodnie z oczekiwaniami)
- **psycopg2** — adapter PostgreSQL
- **PyYAML** — parsowanie konfiguracji
- **python-dotenv** — zmienne środowiskowe
- **Poetry** — zarządzanie zależnościami

## Struktura projektu

```
src/
├── main.py                    # Punkt wejścia
├── config.py                  # Ładowanie konfiguracji
├── database/
│   └── postgresql.py          # Klient PostgreSQL
└── emsairtable/
    ├── airtable_client.py     # Klient API Airtable
    ├── schema_sync.py         # Synchronizacja schematów
    ├── data_sync.py           # Synchronizacja danych
    └── schema_printer.py      # Formatowanie schematów
```

## Testy

```bash
poetry run pytest
```
