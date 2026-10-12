#!/usr/bin/env bash
# Zet de hele stack om naar een nieuw domein. Gebruik: ./scripts/domeinwissel.sh demostack.nl
# Vereist: DNS (A/AAAA voor het domein en *.domein) wijst al naar deze server.
set -euo pipefail
cd "$(dirname "$0")/.."
NEW=${1:?nieuw domein}
OLD=$(grep '^BASE_DOMAIN=' .env | cut -d= -f2)
[ "$OLD" = "$NEW" ] && { echo "Al op $NEW"; exit 0; }
sed -i "s/^BASE_DOMAIN=.*/BASE_DOMAIN=$NEW/" .env
if grep -q '^OUD_DOMEIN=' .env; then sed -i "s/^OUD_DOMEIN=\(.*\)/OUD_DOMEIN=\1 $OLD/" .env; else echo "OUD_DOMEIN=$OLD" >> .env; fi
set -a; . ./.env; set +a

./scripts/caddyfile.sh | sudo tee /etc/caddy/Caddyfile >/dev/null && sudo systemctl reload caddy
./scripts/render-config.sh
COMPOSE_PROFILES=kcc,gzac,zac docker compose up -d
for _ in $(seq 1 60); do curl -sf "https://keycloak.$NEW/realms/demogemeente/.well-known/openid-configuration" >/dev/null && break; sleep 5; done
docker compose run --rm -T -e OUD_DOMEIN="$OLD" -e BASE_DOMAIN -e ADMIN_PASSWORD -v "$PWD/scripts:/scripts:ro" openforms \
  python /scripts/keycloak_domein.py 2>&1 | grep -vE '^\{"|Container'
./scripts/setup.sh
echo "Omgezet naar https://$NEW/ (oude adressen op $OLD verwijzen door)"
