#!/bin/bash
# Keycloak-inrichting van stack g4, idempotent. Draait met het Keycloak-image (kcadm.sh).
#
# 1. Realm "g4": medewerkers van Gemeente Voorbeeldstad, met de clients van GZAC
#    (valtimo-console, valtimo-user-m2m-client) en IKO, de Valtimo-rollen en twee
#    fictieve medewerkers. Bestaat de realm al, dan worden alleen secrets en
#    wachtwoorden bijgewerkt.
# 2. Realm "voorbeeldstad" (DigiD-simulatie): de clients van NL Portal.
#    - nlportal      publieke client van de frontend (authorization code), met de claim
#                    "bsn" en de backend-client als audience
#    - nlportal-m2m  vertrouwelijke client van de backend. NL Portal wisselt elk
#                    burgertoken in (token exchange v1, RFC 8693) voor een token van deze
#                    client en leest daar de "bsn" uit.
set -euo pipefail

KC=/opt/keycloak/bin/kcadm.sh
for i in $(seq 1 60); do
    if $KC config credentials --server "${KEYCLOAK_URL:-http://keycloak.local:8080}" --realm master \
        --user "${KC_ADMIN_USERNAME:-admin}" --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; then
        break
    fi
    sleep 3
done

vervang() {
    local json="$1" var
    for var in MEDEWERKER_WACHTWOORD KEYCLOAK_GZAC_M2M_SECRET KEYCLOAK_IKO_SECRET \
        KEYCLOAK_NLPORTAL_M2M_SECRET PORT_GZAC PORT_GZAC_BACKEND PORT_IKO PORT_NLPORTAL; do
        json="${json//\$\{$var\}/${!var:?$var ontbreekt}}"
    done
    printf '%s' "$json"
}

# ------------------------------------------------------------------ realm g4
if $KC get realms/g4 >/dev/null 2>&1; then
    echo "realm g4 bestaat al: secrets en wachtwoorden bijwerken"
    for paar in valtimo-user-m2m-client=KEYCLOAK_GZAC_M2M_SECRET iko=KEYCLOAK_IKO_SECRET; do
        cid="${paar%%=*}"; var="${paar#*=}"
        id=$($KC get clients -r g4 -q clientId="$cid" --fields id --format csv --noquotes | head -1)
        $KC update "clients/$id" -r g4 -s "secret=${!var}"
    done
    for gebruiker in behandelaar.bakker beheer.yilmaz; do
        $KC set-password -r g4 --username "$gebruiker" --new-password "$MEDEWERKER_WACHTWOORD"
    done
else
    vervang "$(cat /config/g4-realm.json)" | $KC create realms -f -
    echo "realm g4 aangemaakt"
fi

# ------------------------------------------- NL Portal in realm voorbeeldstad
zet_client() {
    local json="$1" client_id
    client_id=$(printf '%s' "$json" | sed -n 's/^ *"clientId": "\([^"]*\)".*/\1/p' | head -1)
    id=$($KC get clients -r voorbeeldstad -q clientId="$client_id" --fields id --format csv --noquotes | head -1)
    if [ -n "$id" ]; then
        printf '%s' "$json" | $KC update "clients/$id" -r voorbeeldstad -f -
        echo "client bijgewerkt: $client_id"
    else
        printf '%s' "$json" | $KC create clients -r voorbeeldstad -f -
        echo "client aangemaakt: $client_id"
    fi
}

BSN_MAPPER='{"name": "bsn", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-attribute-mapper",
     "config": {"user.attribute": "bsn", "claim.name": "bsn", "jsonType.label": "String",
                "id.token.claim": "true", "access.token.claim": "true", "userinfo.token.claim": "true"}}'
AUDIENCE_M2M='{"name": "audience-nlportal-m2m", "protocol": "openid-connect", "protocolMapper": "oidc-audience-mapper",
     "config": {"included.client.audience": "nlportal-m2m", "id.token.claim": "false", "access.token.claim": "true"}}'

zet_client "$(vervang "$(cat <<JSON
{
  "clientId": "nlportal",
  "name": "NL Portal",
  "enabled": true,
  "publicClient": true,
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": false,
  "redirectUris": ["http://localhost:\${PORT_NLPORTAL}/*", "http://127.0.0.1:\${PORT_NLPORTAL}/*"],
  "webOrigins": ["+"],
  "attributes": {"post.logout.redirect.uris": "+"},
  "protocolMappers": [$BSN_MAPPER, $AUDIENCE_M2M]
}
JSON
)")"

zet_client "$(vervang "$(cat <<JSON
{
  "clientId": "nlportal-m2m",
  "name": "NL Portal backend (token exchange)",
  "enabled": true,
  "publicClient": false,
  "clientAuthenticatorType": "client-secret",
  "secret": "\${KEYCLOAK_NLPORTAL_M2M_SECRET}",
  "standardFlowEnabled": false,
  "directAccessGrantsEnabled": false,
  "serviceAccountsEnabled": false,
  "attributes": {"standard.token.exchange.enabled": "false"},
  "protocolMappers": [$BSN_MAPPER, $AUDIENCE_M2M]
}
JSON
)")"
