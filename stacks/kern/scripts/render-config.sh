#!/usr/bin/env bash
# Rendert config/templates/*.yaml en de Keycloak-realm naar config/generated/ met waarden uit .env.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
mkdir -p config/generated/keycloak
for t in config/templates/*.yaml; do envsubst < "$t" > "config/generated/$(basename "$t")"; done
mkdir -p config/generated/solr
python3 scripts/solr_security.py > config/generated/solr/security.json
python3 scripts/make_realm.py > config/generated/keycloak/demogemeente-realm.json
# KISS: met KISS_ONEGROUND=1 een tweede register met de zaken uit OneGround. KISS herkent een register aan de URL van
# Open Klant; omdat beide registers dezelfde Open Klant delen, krijgt het tweede een slash extra. Gevolg: contactmomenten
# staan dan dubbel in KISS (KISS gaat uit van één zaaksysteem per klantregister).
if [ "${KISS_ONEGROUND:-0}" = 1 ]; then cat > config/generated/kiss-extra.env <<ENV
REGISTERS__1__IS_DEFAULT=false
REGISTERS__1__REGISTRY_VERSION=OpenKlant2
REGISTERS__1__KLANTINTERACTIE_BASE_URL=https://klant.${BASE_DOMAIN}/klantinteracties/
REGISTERS__1__KLANTINTERACTIE_TOKEN=${OK_TOKEN_KISS}
REGISTERS__1__ZAAKSYSTEEM_ZAKEN_BASE_URL=https://og-zaken.${BASE_DOMAIN}/api/v1
REGISTERS__1__ZAAKSYSTEEM_CATALOGI_BASE_URL=https://og-catalogi.${BASE_DOMAIN}/api/v1
REGISTERS__1__ZAAKSYSTEEM_DOCUMENTEN_BASE_URL=https://og-documenten.${BASE_DOMAIN}/api/v1
REGISTERS__1__ZAAKSYSTEEM_API_CLIENT_ID=kiss
REGISTERS__1__ZAAKSYSTEEM_API_KEY=${OG_KISS_SECRET}
REGISTERS__1__ZAAKSYSTEEM_DEEPLINK_URL=https://og-zaken.${BASE_DOMAIN}/swagger/index.html#
REGISTERS__1__ZAAKSYSTEEM_DEEPLINK_PROPERTY=identificatie
ENV
else : > config/generated/kiss-extra.env; fi
# De Maykin-images en Keycloak draaien als uid 1000
chown -R 1000:1000 config/generated; chmod -R go-rwx config/generated
