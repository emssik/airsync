# airsync

> This project is published as part of [PIY — Prompt It Yourself](https://blog.atdpath.com/piy), a personal initiative launched on March 8, 2026, encouraging others to build their own apps with the help of LLMs.

Automatic synchronization of Airtable bases to PostgreSQL. Fetches schemas and data from all available Airtable bases, creates corresponding PostgreSQL tables, and keeps data in sync.

## Features

- Sync multiple Airtable bases at once
- Automatic PostgreSQL table creation based on Airtable schemas
- UPSERT — inserts new records or updates existing ones
- Airtable-to-PostgreSQL type mapping
- Automatic `created_at` and `updated_at` columns
- Dry-run mode — preview changes without writing to the database
- Sync a specific base by ID
- Exclusion list in configuration
- Cron schedule (daily at 2:00 AM)

## Requirements

- Python 3.12+
- Poetry
- PostgreSQL 17
- Docker & Docker Compose (for deployment)

## Environment variables

| Variable | Description |
|---|---|
| `AIRTABLE_API_KEY` | Airtable API key |
| `POSTGRESQL_PASSWORD` | PostgreSQL password |
| `POSTGRES_SCHEMA` | PostgreSQL schema (defaults to `public`) |

## Local installation

```bash
poetry install
```

## Configuration

Copy the example files and fill in your own data:

```bash
cp .env.example .env
cp config.yaml.example config.yaml
```

- `.env` — Airtable API key and PostgreSQL password
- `config.yaml` — database address, user, and list of excluded Airtable bases

## Usage

```bash
# Sync all bases
poetry run python src/main.py

# Sync a specific base
poetry run python src/main.py --base-id APP123

# Preview without writing (dry-run)
poetry run python src/main.py --dry-run
```

## Docker

### Building images

```bash
./docker/build.sh
```

### Production deploy

```bash
docker compose -f compose.prod.yaml up -d
```

## Tech stack

- **pyairtable 2.3.6** — Airtable API client (version 3.0.0 doesn't work as expected)
- **psycopg2** — PostgreSQL adapter
- **PyYAML** — configuration parsing
- **python-dotenv** — environment variables
- **Poetry** — dependency management

## Project structure

```
src/
├── main.py                    # Entry point
├── config.py                  # Configuration loader
├── database/
│   └── postgresql.py          # PostgreSQL client
└── emsairtable/
    ├── airtable_client.py     # Airtable API client
    ├── schema_sync.py         # Schema synchronization
    ├── data_sync.py           # Data synchronization
    └── schema_printer.py      # Schema formatting
```

## Tests

```bash
poetry run pytest
```
