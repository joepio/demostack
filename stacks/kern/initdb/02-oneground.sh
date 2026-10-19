#!/bin/bash
# OneGround (Visma Roxit): rollen, databases en schema's zoals in hun getting-started, maar idempotent.
set -e
[ -n "$OG_DB_ADMIN_PASSWORD" ] || { echo "OneGround overgeslagen (geen OG_DB_ADMIN_PASSWORD)"; exit 0; }
q(){ psql -v ON_ERROR_STOP=1 -U postgres "$@"; }
role(){ q -tAc "SELECT 1 FROM pg_roles WHERE rolname='$1'" | grep -q 1 || q -c "CREATE ROLE $1 WITH LOGIN PASSWORD '$2';"; }
role oneground_admin "$OG_DB_ADMIN_PASSWORD"
role oneground_user "$OG_DB_USER_PASSWORD"
role og_keycloak "$OG_KC_DB_PASSWORD"
q -tAc "SELECT 1 FROM pg_database WHERE datname='og_keycloak'" | grep -q 1 || q -c "CREATE DATABASE og_keycloak OWNER og_keycloak;"
for db in og_ac og_brc og_drc og_nrc og_zrc og_ztc; do
  q -tAc "SELECT 1 FROM pg_database WHERE datname='$db'" | grep -q 1 || q -c "CREATE DATABASE $db;"
  q -d $db <<SQL
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
GRANT CREATE, USAGE ON SCHEMA public TO oneground_admin;
GRANT USAGE ON SCHEMA public TO oneground_user;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE, TRIGGER ON TABLES TO oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO oneground_user;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT SELECT, USAGE, UPDATE ON SEQUENCES TO oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT SELECT, USAGE ON SEQUENCES TO oneground_user;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO oneground_admin, oneground_user;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA public GRANT USAGE ON TYPES TO oneground_admin, oneground_user;
SQL
done
for db in og_drc og_nrc; do
  q -d $db <<SQL
CREATE SCHEMA IF NOT EXISTS hangfire AUTHORIZATION oneground_user;
GRANT ALL ON SCHEMA hangfire TO oneground_user, oneground_admin;
GRANT ALL ON ALL TABLES IN SCHEMA hangfire TO oneground_user, oneground_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA hangfire TO oneground_user, oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA hangfire GRANT ALL ON TABLES TO oneground_user, oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA hangfire GRANT ALL ON SEQUENCES TO oneground_user, oneground_admin;
SQL
done
q -d og_zrc <<SQL
CREATE SCHEMA IF NOT EXISTS data_protection AUTHORIZATION oneground_user;
GRANT ALL ON SCHEMA data_protection TO oneground_user, oneground_admin;
GRANT ALL ON ALL TABLES IN SCHEMA data_protection TO oneground_user, oneground_admin;
GRANT ALL ON ALL SEQUENCES IN SCHEMA data_protection TO oneground_user, oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA data_protection GRANT ALL ON TABLES TO oneground_user, oneground_admin;
ALTER DEFAULT PRIVILEGES FOR ROLE oneground_admin IN SCHEMA data_protection GRANT ALL ON SEQUENCES TO oneground_user, oneground_admin;
SQL
