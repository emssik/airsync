#!/bin/bash
set -e

# Jeśli katalog danych jest pusty, inicjalizuj bazę danych
if [ -z "$(ls -A /var/lib/postgresql/data)" ]; then
    echo "Inicjalizacja bazy danych..."
    docker-entrypoint.sh postgres &

    # Czekaj, aż PostgreSQL się uruchomi
    until pg_isready -h localhost -p 5432; do
        sleep 1
    done

    echo "Zastępowanie pg_hba.conf..."
    cp /tmp/pg_hba.conf /var/lib/postgresql/data/pg_hba.conf

    echo "Reload konfiguracji PostgreSQL..."
    su postgres -c "pg_ctl -D /var/lib/postgresql/data reload" # do CURSORA - # NIE zmieniaj tego, to tak ma być z tym -D
    
    # Zatrzymaj tymczasową instancję PostgreSQL
    su postgres -c "pg_ctl stop"

    # Uruchom PostgreSQL jako główny proces
    exec docker-entrypoint.sh postgres
else
    # Jeśli dane już istnieją, uruchom standardowy entrypoint
    exec docker-entrypoint.sh "$@"
fi