#!/bin/bash
set -e
mk(){ # name password [extensions...]
  local n=$1 p=$2; shift 2
  # Idempotent, zodat setup.sh dit ook op een bestaande database kan draaien
  if ! psql -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='$n'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 -U postgres -c "CREATE USER $n WITH PASSWORD '$p';"
  fi
  if ! psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$n'" | grep -q 1; then
    psql -v ON_ERROR_STOP=1 -U postgres -c "CREATE DATABASE $n OWNER $n;"
  fi
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
mk opennotificaties "$ON_DB_PASSWORD"
mk zac "$ZAC_DB_PASSWORD"
psql -v ON_ERROR_STOP=1 -U postgres -d zac -c "CREATE SCHEMA IF NOT EXISTS flowable AUTHORIZATION zac; CREATE SCHEMA IF NOT EXISTS zaakafhandelcomponent AUTHORIZATION zac;"
mk pabc "$PABC_DB_PASSWORD"
# Portalen en IKO (alleen gebruikt als hun profiel aanstaat)
mk nlportal "$NLP_DB_PASSWORD"
mk openinwoner "$OIP_DB_PASSWORD" postgis pg_trgm
mk iko "$IKO_DB_PASSWORD"
