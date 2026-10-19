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
    for v in ON_DB_PASSWORD; do echo "$v=$(gen 16)"; done
    echo "ON_SECRET_KEY=$(gen 30)"
    for v in ON_CLIENT_SECRET OZ_TO_ON_SECRET OBJ_TO_ON_SECRET OK_TOKEN_ZAC OBJ_TOKEN_ZAC; do echo "$v=$(gen 20)"; done
    for v in ZAC_DB_PASSWORD PABC_DB_PASSWORD SOLR_PASSWORD OFFICE_CONVERTER_PASSWORD; do echo "$v=$(gen 16)"; done
    for v in BEHEER_OIDC_SECRET DIGID_OIDC_SECRET ZAC_OIDC_SECRET ZAC_ADMIN_SECRET PABC_OIDC_SECRET PABC_ADMIN_SECRET PABC_API_KEY ZAC_ZGW_SECRET ZAC_ON_KEY ZAC_INTERNAL_KEY; do echo "$v=$(gen 24)"; done
    for v in KISS_OT_AFDELING KISS_OT_GROEP KISS_OT_MEDEWERKER KISS_OT_VAC KISS_OT_KENNISARTIKEL; do echo "$v="; done
  } > .env
  echo "Nieuwe .env aangemaakt."
fi
# Geheimen voor later toegevoegde onderdelen aanvullen in een bestaande .env
for v in NLP_DB_PASSWORD OIP_DB_PASSWORD IKO_DB_PASSWORD VTB_DB_PASSWORD OG_DB_ADMIN_PASSWORD OG_DB_USER_PASSWORD OG_KC_DB_PASSWORD OG_KC_ADMIN_PASSWORD OG_RABBIT_PASSWORD OG_DP_CERT_PASSWORD OG_SERVICE_SECRET OG_OF_SECRET OG_NLP_SECRET OG_KISS_SECRET; do grep -q "^$v=" .env || echo "$v=$(gen 16)" >> .env; done
# API-tokens van Objecten en Open Klant zijn maximaal 40 tekens
for v in NLP_OBJ_TOKEN NLP_OK_TOKEN OIP_OBJ_TOKEN OIP_OT_TOKEN OIP_OK_TOKEN MO_OBJ_TOKEN VTB_TOKEN_DEMO; do grep -q "^$v=" .env || echo "$v=$(gen 20)" >> .env; done
# NL Portal kiest het JWT-algoritme op sleutellengte; Open Zaak accepteert alleen HS256, dus precies 32 tekens
grep -q "^VTB_SECRET_KEY=" .env || echo "VTB_SECRET_KEY=$(gen 30)" >> .env
grep -q "^NLP_ZGW_SECRET=" .env || echo "NLP_ZGW_SECRET=$(gen 16)" >> .env
for v in DEMO_LOGIN_SECRET ZAAKCHAT_JWT_SECRET ZAAKCHAT_OIDC_SECRET ZAAKCHAT_ZGW_SECRET ZAAKCHAT_ON_KEY MO_SESSION_SECRET MO_ZGW_SECRET NLP_M2M_SECRET OIP_SECRET_KEY OIP_ZGW_SECRET OIP_NC_SECRET IKO_OIDC_SECRET IKO_CRYPTO_KEY; do grep -q "^$v=" .env || echo "$v=$(gen 24)" >> .env; done
# OneGround: HMAC-sleutel en certificaat voor het versleuteld opslaan van BSN's in de Zaken API
grep -q "^OG_HMAC_KEY=" .env || echo "OG_HMAC_KEY=$(openssl rand -base64 32)" >> .env
if ! grep -q "^OG_DP_CERT=" .env; then
  T=$(mktemp -d); P=$(grep '^OG_DP_CERT_PASSWORD=' .env | cut -d= -f2)
  openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -subj "/CN=oneground-dataprotection" -keyout "$T/k.pem" -out "$T/c.pem" 2>/dev/null
  openssl pkcs12 -export -inkey "$T/k.pem" -in "$T/c.pem" -out "$T/dp.pfx" -passout "pass:$P"
  echo "OG_DP_CERT=$(base64 -w0 "$T/dp.pfx")" >> .env; rm -rf "$T"
fi
grep -q '^COMPOSE_PROFILES=' .env || echo "COMPOSE_PROFILES=kcc,gzac,zac,oip,nlportal,mijnoverheid,iko,zaakchat,oneground,openvtb" >> .env
set -a; . ./.env; set +a
# Tijdens de setup draaien alle werkplekken; aan het eind gelden weer de profielen uit .env
WANTED_PROFILES=$COMPOSE_PROFILES; export COMPOSE_PROFILES=kcc,gzac,zac,oip,nlportal,mijnoverheid,iko,zaakchat,oneground,openvtb
setenv() { if grep -q "^$1=" .env; then sed -i "s|^$1=.*|$1=$2|" .env; else echo "$1=$2" >> .env; fi; }
q() { grep -v -E '^\{"|Container|^$' || true; }

./scripts/render-config.sh
docker compose up -d db redis
for _ in $(seq 1 30); do docker compose exec -T db pg_isready -U postgres >/dev/null 2>&1 && break; sleep 2; done
# Databases voor later toegevoegde onderdelen ook in een bestaande installatie aanmaken (idempotent)
docker compose exec -T db bash /docker-entrypoint-initdb.d/01-databases.sh 2>&1 | grep -vE "already exists|^CREATE|^$" || true
docker compose exec -T -e OG_DB_ADMIN_PASSWORD -e OG_DB_USER_PASSWORD -e OG_KC_DB_PASSWORD db bash /docker-entrypoint-initdb.d/02-oneground.sh 2>&1 \
  | grep -vE "already exists|^(CREATE|GRANT|ALTER)|^$" || true
docker compose up -d

wait_http() { # poort pad
  for _ in $(seq 1 90); do
    code=$(curl -s -o /dev/null -w '%{http_code}' -H 'Host: localhost' "http://127.0.0.1:$1$2" || true)
    case "$code" in 200|302) return 0;; esac; sleep 5
  done; echo "Timeout op poort $1"; exit 1
}
for p in 8101 8102 8103 8104 8105 8110 8113; do wait_http $p /admin/login/; done

apply() { # service template
  echo "== setup_configuration $1 ($2)"
  docker compose run --rm -T -v "$PWD/config/generated/$2.yaml:/app/setup_configuration/data.yaml:ro" "$1" \
    src/manage.py setup_configuration --yaml-file setup_configuration/data.yaml 2>&1 | grep -E "Success|rror|completed" || true
}
apply opennotificaties opennotificaties; apply openzaak openzaak; apply objecttypes objecttypes; apply objects objects; apply openforms openforms; apply openklant openklant

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
setenv TAAK_OT "$(echo "$UUIDS" | python3 -c "import json,sys;print(json.load(sys.stdin)['Taak'])")"
# Actor in Open Klant waarnamens Open Inwoner vragen registreert
if ! grep -q '^OIP_OK_ACTOR=.' .env; then
  setenv OIP_OK_ACTOR "$(curl -s -X POST "https://klant.$BASE_DOMAIN/klantinteracties/api/v1/actoren" -H "Authorization: Token $OK_TOKEN_KISS" \
    -H "Content-Type: application/json" -d '{"naam":"Open Inwoner","soortActor":"geautomatiseerde_actor","indicatieActief":true,"actoridentificator":{"objectId":"open-inwoner","codeObjecttype":"app","codeRegister":"demogemeente","codeSoortObjectId":"client_id"}}' \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['uuid'])")"
fi
set -a; . ./.env; set +a
./scripts/render-config.sh
apply objects objects-kiss
docker compose up -d kiss

TOKEN=$(docker compose exec -T openforms python src/manage.py drf_create_token admin 2>/dev/null | grep -oE '[0-9a-f]{40}')
GID=$(docker compose exec -T openforms python src/manage.py shell -c \
  "from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig as Z; print(Z.objects.get(identifier='demogemeente').pk)" 2>/dev/null | tail -1)
run_seed objects seed_kiss_objecten.py -e OBJ_TOKEN_KISS -e KISS_OT_AFDELING -e KISS_OT_GROEP -e KISS_OT_MEDEWERKER -e KISS_OT_VAC -e KISS_OT_KENNISARTIKEL
run_seed openzaak seed_testpersoon.py -e OZ_DEMO_SECRET
run_seed openzaak seed_meldingen.py -e OZ_DEMO_SECRET
# DigiD (demo) via Keycloak: testinwoners met BSN; Open Formulieren gebruikt het als DigiD-login
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e DIGID_OIDC_SECRET -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_digid.py 2>&1 | q
docker compose exec -T -e BASE_DOMAIN -e DIGID_OIDC_SECRET openforms python src/manage.py shell < scripts/openforms_inrichting.py 2>&1 | grep " ok" || true
OG_GID=$(docker compose exec -T openforms python src/manage.py shell -c \
  "from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig as Z; print(Z.objects.get(identifier='oneground').pk)" 2>/dev/null | tail -1)
run_seed openforms seed_openforms.py -e OF_TOKEN="$TOKEN" -e ZGW_GROUP_ID="$GID" -e OG_GROUP_ID="$OG_GID"
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

# ZAC (Dimpact): Keycloak, zaakafhandelparameters, notificaties en zoekindex
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e ZAC_OIDC_SECRET -e ZAC_ADMIN_SECRET -e PABC_OIDC_SECRET \
  -e PABC_ADMIN_SECRET -v "$PWD/scripts:/scripts:ro" openforms python /scripts/keycloak_zac.py 2>&1 | q
docker compose up -d
for _ in $(seq 1 60); do curl -s http://127.0.0.1:8111/ -o /dev/null -w '%{http_code}' | grep -qE '200|302' && break; sleep 5; done
docker run --rm --network host -e BASE_DOMAIN -e ADMIN_PASSWORD -v "$PWD/scripts/zac_inrichten.py:/t.py:ro" \
  mcr.microsoft.com/playwright/python:v1.55.0-noble sh -c "pip -q install playwright==1.55.0 2>/dev/null; python /t.py" | tail -2
apply opennotificaties opennotificaties-zac
apply opennotificaties opennotificaties-zaakchat
curl -s -o /dev/null -H "X-API-KEY: $ZAC_INTERNAL_KEY" http://127.0.0.1:8111/rest/internal/indexeren/herindexeren/ZAAK

# Inwonerportalen: Keycloak (NL Portal token exchange, nep-DigiD voor Open Inwoner en MijnOverheid), portaaltaak
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e NLP_M2M_SECRET -e ZAAKCHAT_OIDC_SECRET -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_portalen.py 2>&1 | q
run_seed objects seed_portaaltaak.py -e TAAK_OT -e OBJ_TOKEN_KISS -e OZ_DEMO_SECRET
# Open Inwoner: koppelingen via setup_configuration, de rest (BRP, CMS-pagina's, abonnement) via de shell
apply openinwoner openinwoner
docker compose exec -T -e BASE_DOMAIN -e TAAK_OT -e OIP_NC_SECRET openinwoner python src/manage.py shell \
  < scripts/openinwoner_inrichting.py 2>&1 | grep -E " ok|aangemaakt|geregistreerd" || true
docker compose restart openinwoner >/dev/null
# IKO: alleen de SSO-client; connectoren en profielen richt je in het beheerscherm in
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e IKO_OIDC_SECRET -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_iko.py 2>&1 | q

# OneGround: eigen Keycloak (realm, client met rsin-claim), daarna dezelfde demo-catalogus en -meldingen als in Open Zaak
for _ in $(seq 1 60); do curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8137/realms/master | grep -q 200 && break; sleep 5; done
docker compose run --rm -T --no-deps -e OG_KC_ADMIN_PASSWORD -e OG_CLIENTS="oneground-002220647=$OG_SERVICE_SECRET,openforms=$OG_OF_SECRET,nl-portal=$OG_NLP_SECRET,kiss=$OG_KISS_SECRET" \
  -v "$PWD/scripts:/scripts:ro" openforms python /scripts/keycloak_oneground.py 2>&1 | q
docker compose restart og-autorisaties og-catalogi og-zaken og-documenten og-besluiten og-notificaties >/dev/null
for _ in $(seq 1 60); do curl -s -o /dev/null -w '%{http_code}' "https://og-catalogi.$BASE_DOMAIN/api/v1/catalogussen" | grep -q 401 && break; sleep 5; done
# De Documenten-API draait als uid 1654 en schrijft bestanden naar het volume
docker run --rm -v kern_og-documenten:/data alpine:3.23 sh -c "mkdir -p /data/drc_dms && chown -R 1654:1654 /data"
OG="-e CATALOGI_API=https://og-catalogi.$BASE_DOMAIN/api/v1 -e ZAKEN_API=https://og-zaken.$BASE_DOMAIN/api/v1 -e ZGW_CLIENT=oneground-002220647 -e ZGW_SECRET=$OG_SERVICE_SECRET"
run_seed openzaak seed_openzaak.py -e OZ_DEMO_SECRET $OG -e SELECTIELIJST_API="https://og-referentielijsten.$BASE_DOMAIN/api/v1"
run_seed openzaak seed_meldingen.py -e OZ_DEMO_SECRET $OG

# Open VTB: API-account, berichttype en een bericht en twee taken voor Suzanne
wait_http 8121 /admin/login/
docker compose exec -T -e VTB_TOKEN_DEMO -e BASE_DOMAIN openvtb python src/manage.py shell < scripts/seed_openvtb.py 2>&1 \
  | grep -E "^aangemaakt|^/" || true

# Single sign-on: account 'demo', langere sessies, beheerschermen via Keycloak
docker compose run --rm -T -e BASE_DOMAIN -e ADMIN_PASSWORD -e BEHEER_OIDC_SECRET -e DEMO_LOGIN_SECRET -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_sso.py 2>&1 | q
for s in openzaak openklant objects objecttypes opennotificaties openvtb; do apply $s oidc; done
apply openforms oidc-openforms

python3 welkom/evaluatie.py || true
KISS=1 KISS_VERSION=3.2.0 ./welkom/build.sh
./welkom/screenshots.sh || echo "Screenshots mislukt; de welkomstpagina werkt ook zonder."
sed -i "s/^COMPOSE_PROFILES=.*/COMPOSE_PROFILES=$WANTED_PROFILES/" .env
./scripts/stack.sh toepassen
echo "Klaar. Welkomstpagina: https://$BASE_DOMAIN/ (Caddy-config: scripts/caddyfile.sh)"
