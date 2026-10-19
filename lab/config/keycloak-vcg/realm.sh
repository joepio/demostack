#!/bin/bash
# Maakt realm "vcg" (medewerkers van Gemeente Voorbeeldstad) aan in Keycloak, met de
# clients van Open Beheer en Open Organisatie, rollen en vijf fictieve medewerkers: de
# vier behandelaars uit de seed (seed/data.py, MEDEWERKERS) en een functioneel
# beheerder. Idempotent: bestaat de realm al, dan worden alleen de client-secrets en
# wachtwoorden bijgewerkt. Draait met het Keycloak-image (kcadm.sh).
set -euo pipefail

KC=/opt/keycloak/bin/kcadm.sh
for i in $(seq 1 60); do
    if $KC config credentials --server "${KEYCLOAK_URL:-http://keycloak.local:8080}" --realm master \
        --user "${KC_ADMIN_USERNAME:-admin}" --password "$KC_ADMIN_PASSWORD" >/dev/null 2>&1; then
        break
    fi
    sleep 3
done

json="$(cat /config/vcg-realm.json)"
for var in MEDEWERKER_WACHTWOORD KEYCLOAK_OPENBEHEER_CLIENT_SECRET KEYCLOAK_OPENORGANISATIE_CLIENT_SECRET \
    PORT_OPENBEHEER PORT_OPENORGANISATIE; do
    json="${json//\$\{$var\}/${!var:?$var ontbreekt}}"
done

if $KC get realms/vcg >/dev/null 2>&1; then
    echo "realm vcg bestaat al: secrets en wachtwoorden bijwerken"
    for cid in openbeheer openorganisatie; do
        var="KEYCLOAK_${cid^^}_CLIENT_SECRET"
        id=$($KC get clients -r vcg -q clientId="$cid" --fields id --format csv --noquotes | head -1)
        $KC update "clients/$id" -r vcg -s "secret=${!var}"
    done
    for gebruiker in a.vermeulen s.bakker r.vandijk l.smits beheer.devos; do
        $KC set-password -r vcg --username "$gebruiker" --new-password "$MEDEWERKER_WACHTWOORD"
    done
else
    echo "$json" | $KC create realms -f -
    echo "realm vcg aangemaakt"
fi

# Inlogflow "beheer-browser" voor de beheerclients (Open Beheer, Open Organisatie): eerst
# gewoon inloggen (SSO-cookie of gebruikersnaam en wachtwoord), daarna een rolcontrole:
# wie de realmrol Functioneel-Beheerder niet heeft, wordt geweigerd. Open Beheer 0.9.0
# laat elke ingelogde gebruiker de Catalogi API beheren (DRF IsAuthenticated); zonder
# deze flow zou elke behandelaar zaaktypen kunnen wijzigen. Elke stap is idempotent.
uitvoering() {  # uitvoering <flow-alias> <displayName>: id van die stap (of leeg)
    local id naam
    while IFS=, read -r id naam; do
        [ "$naam" = "$2" ] && { echo "$id"; return; }
    done < <($KC get "authentication/flows/$1/executions" -r vcg --fields id,displayName --format csv --noquotes)
    return 0
}
stap() {  # stap <flow-alias> <displayName> <requirement> <flow|execution> <alias-of-provider>
    local id
    id=$(uitvoering "$1" "$2")
    if [ -z "$id" ]; then
        if [ "$4" = flow ]; then
            $KC create "authentication/flows/$1/executions/flow" -r vcg -s "alias=$5" -s type=basic-flow >/dev/null
        else
            $KC create "authentication/flows/$1/executions/execution" -r vcg -s "provider=$5" >/dev/null
        fi
        id=$(uitvoering "$1" "$2")
    fi
    $KC update "authentication/flows/$1/executions" -r vcg -b "{\"id\":\"$id\",\"requirement\":\"$3\"}"
    echo "$id"
}
config() {  # config <flow-alias> <execution-id> <alias> <sleutel=waarde>...
    local flow="$1" id="$2" alias="$3" eid cfg; shift 3
    while IFS=, read -r eid cfg; do
        [ "$eid" = "$id" ] && [ -n "$cfg" ] && return 0
    done < <($KC get "authentication/flows/$flow/executions" -r vcg --fields id,authenticationConfig \
        --format csv --noquotes)
    local args=()
    for kv in "$@"; do args+=(-s "config.$kv"); done
    $KC create "authentication/executions/$id/config" -r vcg -s "alias=$alias" "${args[@]}" >/dev/null
}
if ! $KC get authentication/flows -r vcg --fields alias --format csv --noquotes | grep -qx beheer-browser; then
    $KC create authentication/flows -r vcg -s alias=beheer-browser -s providerId=basic-flow -s topLevel=true \
        -s builtIn=false -s "description=Inloggen plus rolcontrole Functioneel-Beheerder" >/dev/null
fi
stap beheer-browser beheer-inloggen REQUIRED flow beheer-inloggen >/dev/null
stap beheer-inloggen Cookie ALTERNATIVE execution auth-cookie >/dev/null
stap beheer-inloggen beheer-formulier ALTERNATIVE flow beheer-formulier >/dev/null
stap beheer-formulier "Username Password Form" REQUIRED execution auth-username-password-form >/dev/null
stap beheer-browser beheer-rolcontrole CONDITIONAL flow beheer-rolcontrole >/dev/null
cond=$(stap beheer-rolcontrole "Condition - user role" REQUIRED execution conditional-user-role)
config beheer-rolcontrole "$cond" geen-functioneel-beheerder condUserRole=Functioneel-Beheerder negate=true
weiger=$(stap beheer-rolcontrole "Deny access" REQUIRED execution deny-access-authenticator)
config beheer-rolcontrole "$weiger" alleen-functioneel-beheer \
    "denyErrorMessage=Alleen functioneel beheerders hebben toegang tot deze beheeromgeving."
flow_id=""
while IFS=, read -r id alias; do
    [ "$alias" = beheer-browser ] && flow_id="$id"
done < <($KC get authentication/flows -r vcg --fields id,alias --format csv --noquotes)
for cid in openbeheer openorganisatie; do
    id=$($KC get clients -r vcg -q clientId="$cid" --fields id --format csv --noquotes | head -1)
    $KC update "clients/$id" -r vcg -s "authenticationFlowBindingOverrides.browser=$flow_id"
done
echo "inlogflow beheer-browser (rolcontrole Functioneel-Beheerder) op openbeheer en openorganisatie"
