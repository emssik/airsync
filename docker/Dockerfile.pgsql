FROM postgres:17-alpine

# Kopiowanie skryptu inicjalizacyjnego
COPY docker/init.sql /docker-entrypoint-initdb.d/

# Ustawienie domyślnej strefy czasowej
ENV TZ=Europe/Warsaw

# Expose portu 5435 dla PostgreSQL
EXPOSE 5435