FROM postgres:17-alpine

# Kopiowanie skryptu inicjalizacyjnego
COPY docker/init.sql /docker-entrypoint-initdb.d/
COPY docker/pg_hba.conf /tmp/pg_hba.conf
COPY docker/custom-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/custom-entrypoint.sh

# Ustawienie domyślnej strefy czasowej
ENV TZ=Europe/Warsaw

# Expose portu 5435 dla PostgreSQL
EXPOSE 5432

ENTRYPOINT ["custom-entrypoint.sh"]
CMD ["postgres"]