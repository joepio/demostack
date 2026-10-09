#!/usr/bin/env bash
# Zet de stack "kern" op van nul, of brengt een bestaande installatie bij (idempotent).
# Gebruik: BASE_DOMAIN=demo.example.nl ./scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

gen() { openssl rand -hex "${1:-20}"; }
if [ ! -f .env ]; then
  : "${BASE_DOMAIN:?Zet BASE_DOMAIN, bijvoorbeeld BASE_DOMAIN=demo.example.nl}"
  umask 077
  {
    echo "BASE_DOMAIN=$BASE_DOMAIN"
    echo "ADMIN_PASSWORD=$(gen 10)"
    for v in PG_SUPER_PASSWORD OZ_DB_PASSWORD OK_DB_PASSWORD OBJ_DB_PASSWORD OT_DB_PASSWORD OF_DB_PASSWORD \
             KC_DB_PASSWORD KISS_DB_PASSWORD ELASTIC_PASSWORD; do echo "$v=$(gen 16)"; done
    for v in OZ_SECRET_KEY OK_SECRET_KEY OBJ_SECRET_KEY OT_SECRET_KEY OF_SECRET_KEY; do echo "$v=$(gen 30)"; done
    for v in OZ_OPENFORMS_SECRET OZ_DEMO_SECRET OT_TOKEN_OBJECTS OT_TOKEN_OPENFORMS OT_TOKEN_SEED \
             OBJ_TOKEN_OPENFORMS OBJ_TOKEN_KISS OK_TOKEN_KISS; do echo "$v=$(gen 20)"; done
    for v in KISS_OIDC_SECRET KISS_ZGW_SECRET KISS_MI_KEY GZAC_M2M_SECRET; do echo "$v=$(gen 24)"; done
    for v in GZAC_DB_PASSWORD GZAC_OPERATON_PASSWORD GZAC_ACTUATOR_PASSWORD; do echo "$v=$(gen 16)"; done
    echo "GZAC_PLUGIN_SECRET=$(gen 8)"   # precies 16 tekens
    for v in KISS_OT_AFDELING KISS_OT_GROEP KISS_OT_MEDEWERKER KISS_OT_VAC KISS_OT_KENNISARTIKEL; do echo "$v="; done
  } > .env
  echo "Nieuwe .env aangemaakt."
fi
set -a; . ./.env; set +a
setenv() { if grep -q "^$1=" .env; then sed -i "s|^$1=.*|$1=$2|" .env; else echo "$1=$2" >> .env; fi; }
q() { grep -v -E '^\{"|Container|^$' || true; }

./scripts/render-config.sh
docker compose up -d

wait_http() { # poort pad
  for _ in $(seq 1 90); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: localhost' "http://127.0.0.1:$1$2" || true)
    case "$code" in 200|302) return 0;; esac; sleep 5
  done; echo "Timeout op poort $1"; exit 1
}
for p in 8101 8102 8103 8104 8105; do wait_http $p /admin/login/; done

apply() { # service template
  echo "== setup_configuration $1 ($2)"
  docker compose run --rm -T -v "$PWD/config/generated/$2.yaml:/app/setup_configuration/data.yaml:ro" "$1" \
    src/manage.py setup_configuration --yaml-file setup_configuration/data.yaml 2>&1 | grep -E "Success|rror|completed" || true
}
apply openzaak openzaak; apply objecttypes objecttypes; apply objects objects; apply openforms openforms; apply openklant openklant

for s in openklant objects objecttypes openforms; do
  docker compose exec -T "$s" python src/manage.py createsuperuser --noinput --username admin --email admin@demogemeente.local >/dev/null 2>&1 || true
done

run_seed() { # service script [extra -e vars...]
  local svc=$1 script=$2; shift 2
  docker compose run --rm -T -e BASE_DOMAIN "$@" -v "$PWD/scripts:/scripts:ro" "$svc" python "/scripts/$script" 2>&1 | q
}
run_seed openzaak seed_openzaak.py -e OZ_DEMO_SECRET

# KISS-objecttypen: uuids terug in .env, daarna Objecten en KISS bijwerken
UUIDS=$(docker compose run --rm -T -e BASE_DOMAIN -e OT_TOKEN_SEED -v "$PWD/scripts:/scripts:ro" \
  -v "$PWD/config/objecttypes-schemas:/schemas:ro" objects python /scripts/seed_kiss_objecttypes.py 2>/dev/null | tail -1)
for n in Afdeling Groep Medewerker VAC Kennisartikel; do
  setenv "KISS_OT_$(echo $n | tr a-z A-Z)" "$(echo "$UUIDS" | python3 -c "import json,sys;print(json.load(sys.stdin)['$n'])")"
done
set -a; . ./.env; set +a
./scripts/render-config.sh
apply objects objects-kiss
docker compose up -d kiss

TOKEN=$(docker compose exec -T openforms python src/manage.py drf_create_token admin 2>/dev/null | grep -oE '[0-9a-f]{40}')
GID=$(docker compose exec -T openforms python src/manage.py shell -c \
  "from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig as Z; print(Z.objects.get(identifier='demogemeente').pk)" 2>/dev/null | tail -1)
run_seed openforms seed_openforms.py -e OF_TOKEN="$TOKEN" -e ZGW_GROUP_ID="$GID"
run_seed objects seed_kiss_objecten.py -e OBJ_TOKEN_KISS -e KISS_OT_AFDELING -e KISS_OT_GROEP -e KISS_OT_MEDEWERKER -e KISS_OT_VAC -e KISS_OT_KENNISARTIKEL
run_seed openzaak seed_testpersoon.py -e OZ_DEMO_SECRET
run_seed openforms seed_mail.py

wait_http 8108 /healthz
envsubst < scripts/seed_kiss.sql.tmpl | docker compose exec -T db psql -U postgres -d kiss -q -v ON_ERROR_STOP=1
docker compose run --rm -T kiss-sync-vac >/dev/null 2>&1 && docker compose run --rm -T kiss-sync-smoelenboek >/dev/null 2>&1

# GZAC: Keycloak-clients, -rollen en -gebruikers, daarna dossierrechten voor ROLE_USER
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e GZAC_M2M_SECRET -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_gzac.py 2>&1 | q
docker compose up -d gzac-backend gzac
for _ in $(seq 1 60); do docker compose logs gzac-backend 2>&1 | grep -q "Started ApplicationKt" && break; sleep 5; done
docker run --rm --network host -e BASE_DOMAIN -e ADMIN_PASSWORD -v "$PWD/scripts/gzac_permissions.py:/t.py:ro" \
  mcr.microsoft.com/playwright/python:v1.55.0-noble sh -c "pip -q install playwright==1.55.0 2>/dev/null; python /t.py" | tail -1

KISS=1 KISS_VERSION=3.2.0 ./welkom/build.sh
./welkom/screenshots.sh || echo "Screenshots mislukt; de welkomstpagina werkt ook zonder."
echo "Klaar. Welkomstpagina: https://$BASE_DOMAIN/ (Caddy-config: scripts/caddyfile.sh)"
