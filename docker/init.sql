-- Utworzenie użytkownika z prawami
CREATE USER emssik WITH PASSWORD '${POSTGRES_PASSWORD}' CREATEDB;

-- Utworzenie bazy danych
CREATE DATABASE airsync;

-- Zmiana właściciela bazy danych
ALTER DATABASE airsync OWNER TO emssik; 