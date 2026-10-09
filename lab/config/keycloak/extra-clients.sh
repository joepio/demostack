#!/bin/bash
# Voegt OIDC-clients toe aan realm "voorbeeldstad" (DigiD-simulatie), idempotent.
# Draait in een eenmalige container met het Keycloak-image (kcadm.sh), na de start van
# Keycloak. Gebruik:
#   extra-clients.sh <clientId>=<naam>=<env-var met secret>=<redirect-URI,...> ...
# Elke client is vertrouwelijk (client secret), gebruikt de authorization code flow en
# krijgt de claims "bsn" (gebruikersattribuut) en "loa" (vast: DigiD Substantieel).
set -euo pipefail

KC=/opt/keycloak/bin/kcadm.sh
for i in $(seq 1 60); do
    if $KC config credentials --server "${KEYCLOAK_URL:-http://keycloak.local:8080}" --realm master \
        --user "${KC_ADMIN_USERNAME:-admin}" --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; then
        break
    fi
    sleep 3
done

for spec in "$@"; do
    IFS='=' read -r client_id naam secret_var redirects <<< "$spec"
    secret="${!secret_var:?$secret_var ontbreekt}"
    uris=$(printf '"%s",' ${redirects//,/ })
    json=$(cat <<JSON
{
  "clientId": "$client_id",
  "name": "$naam",
  "enabled": true,
  "publicClient": false,
  "clientAuthenticatorType": "client-secret",
  "secret": "$secret",
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": false,
  "redirectUris": [${uris%,}],
  "attributes": {"post.logout.redirect.uris": "+"},
  "protocolMappers": [
    {"name": "bsn", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-attribute-mapper",
     "config": {"user.attribute": "bsn", "claim.name": "bsn", "jsonType.label": "String",
                "id.token.claim": "true", "access.token.claim": "true", "userinfo.token.claim": "true"}},
    {"name": "betrouwbaarheidsniveau", "protocol": "openid-connect", "protocolMapper": "oidc-hardcoded-claim-mapper",
     "config": {"claim.name": "loa", "claim.value": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "true",
                "userinfo.token.claim": "true"}}
  ]
}
JSON
)
    id=$($KC get clients -r voorbeeldstad -q clientId="$client_id" --fields id --format csv --noquotes | head -1)
    if [ -n "$id" ]; then
        echo "$json" | $KC update "clients/$id" -r voorbeeldstad -f -
        echo "client bijgewerkt: $client_id"
    else
        echo "$json" | $KC create clients -r voorbeeldstad -f -
        echo "client aangemaakt: $client_id"
    fi
done
