CREATE USER openinwoner PASSWORD 'openinwoner';
CREATE DATABASE openinwoner OWNER openinwoner;
CREATE USER openklant PASSWORD 'openklant';
CREATE DATABASE openklant OWNER openklant;
CREATE USER oneground_user PASSWORD 'oneground_user';
CREATE USER oneground_admin PASSWORD 'oneground_admin' SUPERUSER;
CREATE DATABASE grc_db OWNER oneground_admin;
\c openinwoner
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
\c openklant
CREATE EXTENSION IF NOT EXISTS postgis;
