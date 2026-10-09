#!/bin/bash
set -e
mk(){ # name password [extensions...]
  local n=$1 p=$2; shift 2
  psql -v ON_ERROR_STOP=1 -U postgres <<SQL
CREATE USER $n WITH PASSWORD '$p';
CREATE DATABASE $n OWNER $n;
SQL
  for e in "$@"; do psql -v ON_ERROR_STOP=1 -U postgres -d $n -c "CREATE EXTENSION IF NOT EXISTS $e;"; done
}
mk openzaak "$OZ_DB_PASSWORD" postgis pg_trgm
mk openklant "$OK_DB_PASSWORD" pg_trgm
mk objects "$OBJ_DB_PASSWORD" postgis pg_trgm
mk objecttypes "$OT_DB_PASSWORD"
mk openforms "$OF_DB_PASSWORD" pg_trgm
mk keycloak "$KC_DB_PASSWORD"
mk kiss "$KISS_DB_PASSWORD"
mk gzac "$GZAC_DB_PASSWORD"
