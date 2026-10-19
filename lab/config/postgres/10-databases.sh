#!/bin/bash
# Maakt per component een eigen database en gebruiker aan in de gedeelde
# Postgres/PostGIS-instantie. Draait alleen bij de eerste start (leeg volume).
set -euo pipefail

: "${DB_APP_PASSWORD:?DB_APP_PASSWORD ontbreekt}"

maak_db() {
    local naam="$1"; shift
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-SQL
        CREATE USER ${naam} WITH PASSWORD '${DB_APP_PASSWORD}';
        CREATE DATABASE ${naam} OWNER ${naam};
SQL
    for ext in "$@"; do
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$naam" \
            -c "CREATE EXTENSION IF NOT EXISTS ${ext};"
    done
}

maak_db openzaak postgis pg_trgm
maak_db opennotificaties
maak_db openobject postgis
maak_db openklant
maak_db openproduct
maak_db referentielijsten
maak_db selectielijst
maak_db keycloak

# Extra databases per stack: DB_EXTRA in stacks/<naam>/stack.env, spatie-gescheiden,
# elk als naam of naam:extensie,extensie (bijvoorbeeld "openforms openinwoner:postgis").
for item in ${DB_EXTRA:-}; do
    naam="${item%%:*}"
    exts=""
    [[ "$item" == *:* ]] && exts="${item#*:}"
    # shellcheck disable=SC2086
    maak_db "$naam" ${exts//,/ }
done
