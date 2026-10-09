#!/usr/bin/env bash
# Rendert config/templates/*.yaml en de Keycloak-realm naar config/generated/ met waarden uit .env.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; . ./.env; set +a
mkdir -p config/generated/keycloak
for t in config/templates/*.yaml; do envsubst < "$t" > "config/generated/$(basename "$t")"; done
python3 scripts/make_realm.py > config/generated/keycloak/demogemeente-realm.json
# De Maykin-images en Keycloak draaien als uid 1000
chown -R 1000:1000 config/generated; chmod -R go-rwx config/generated
