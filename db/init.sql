CREATE TABLE hba ( lines text );
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf';
INSERT INTO hba (lines) VALUES ('host replication all 0.0.0.0/0 password');
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf';
SELECT pg_reload_conf();

CREATE ROLE repl_user WITH PASSWORD 'Qq12345' REPLICATION;
ALTER ROLE "repl_user" WITH LOGIN;
SELECT pg_create_physical_replication_slot('replication_slot');

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'main_base') THEN
    CREATE DATABASE main_base;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS phonenumbers (
    id SERIAL PRIMARY KEY,
    phonenumber VARCHAR (100) NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR (100) NOT NULL
);
