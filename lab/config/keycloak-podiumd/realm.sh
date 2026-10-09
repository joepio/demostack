#!/bin/bash
# Maakt realm "podiumd" (medewerkers van Gemeente Voorbeeldstad) aan in Keycloak, met
# de clients van KISS, ITA, PABC, Open Archiefbeheer en Open Beheer, de PodiumD-rollen
# en drie fictieve medewerkers. Idempotent: bestaat de realm al, dan worden alleen de
# client-secrets en wachtwoorden bijgewerkt. Draait met het Keycloak-image (kcadm.sh).
#
# In PodiumD heet deze realm ook "podiumd"; daar koppelt hij aan Entra ID of ADFS.
# Hier logt een medewerker direct in Keycloak in.
set -euo pipefail

KC=/opt/keycloak/bin/kcadm.sh
for i in $(seq 1 60); do
    if $KC config credentials --server "${KEYCLOAK_URL:-http://keycloak.local:8080}" --realm master \
        --user "${KC_ADMIN_USERNAME:-admin}" --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; then
        break
    fi
    sleep 3
done

# ${VAR}-plaatshouders vervangen door de omgeving (alleen bekende namen)
json="$(cat /config/podiumd-realm.json)"
for var in MEDEWERKER_WACHTWOORD KEYCLOAK_KISS_CLIENT_SECRET KEYCLOAK_ITA_CLIENT_SECRET \
    KEYCLOAK_PABC_CLIENT_SECRET KEYCLOAK_OPENARCHIEFBEHEER_CLIENT_SECRET \
    KEYCLOAK_OPENBEHEER_CLIENT_SECRET PORT_KISS PORT_ITA PORT_PABC PORT_OPENARCHIEFBEHEER \
    PORT_OPENBEHEER; do
    json="${json//\$\{$var\}/${!var:?$var ontbreekt}}"
done

if $KC get realms/podiumd >/dev/null 2>&1; then
    echo "realm podiumd bestaat al: secrets en wachtwoorden bijwerken"
    for cid in kiss ita pabc openarchiefbeheer openbeheer; do
        var="KEYCLOAK_${cid^^}_CLIENT_SECRET"
        id=$($KC get clients -r podiumd -q clientId="$cid" --fields id --format csv --noquotes | head -1)
        $KC update "clients/$id" -r podiumd -s "secret=${!var}"
    done
    for gebruiker in kcm.jansen behandelaar.desai beheer.devries; do
        $KC set-password -r podiumd --username "$gebruiker" --new-password "$MEDEWERKER_WACHTWOORD"
    done
else
    echo "$json" | $KC create realms -f -
    echo "realm podiumd aangemaakt"
fi
