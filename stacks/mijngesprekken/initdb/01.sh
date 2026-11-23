#!/bin/sh
# Maakt de databases en gebruikers aan bij een lege volume. Wachtwoord uit .env (MG_DB_PASSWORD).
set -e
psql -v ON_ERROR_STOP=1 -U postgres -v pw="$MG_DB_PASSWORD" <<'SQL'
CREATE USER openinwoner PASSWORD :'pw';
CREATE DATABASE openinwoner OWNER openinwoner;
CREATE USER openklant PASSWORD :'pw';
CREATE DATABASE openklant OWNER openklant;
CREATE USER oneground_user PASSWORD :'pw';
CREATE USER oneground_admin PASSWORD :'pw' SUPERUSER;
CREATE DATABASE grc_db OWNER oneground_admin;
\c openinwoner
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\c openklant
CREATE EXTENSION IF NOT EXISTS postgis;
SQL
