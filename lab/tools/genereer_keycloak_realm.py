"""Genereert config/keycloak/voorbeeldstad-realm.json uit de BRP-testdata.

De realm "voorbeeldstad" simuleert een DigiD-inlog: elke fictieve inwoner
heeft als gebruikersnaam zijn test-BSN en krijgt in het token een claim
"bsn". Wachtwoorden en client-secrets zijn placeholders (${...}) die Keycloak
bij de import uit omgevingsvariabelen invult.

Gebruik: python3 tools/genereer_keycloak_realm.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INWONERS = ["999990627", "999997609", "999993409", "999995406", "999991991"]

brp = {p["burgerservicenummer"]: p for p in json.load(open(ROOT / "config/brp/test-data.json", encoding="utf-8"))}

user_profile = {
    "unmanagedAttributePolicy": "ENABLED",
    "attributes": [
        {"name": "username", "displayName": "${username}", "permissions": {"view": ["admin", "user"], "edit": ["admin"]}, "multivalued": False},
        {"name": "email", "displayName": "${email}", "permissions": {"view": ["admin", "user"], "edit": ["admin", "user"]}, "multivalued": False},
        {"name": "firstName", "displayName": "${firstName}", "permissions": {"view": ["admin", "user"], "edit": ["admin", "user"]}, "multivalued": False},
        {"name": "lastName", "displayName": "${lastName}", "permissions": {"view": ["admin", "user"], "edit": ["admin", "user"]}, "multivalued": False},
        {"name": "bsn", "displayName": "BSN", "permissions": {"view": ["admin", "user"], "edit": ["admin"]}, "multivalued": False},
    ],
    "groups": [],
}

users = []
for bsn in INWONERS:
    p = brp[bsn]
    naam = p["naam"]
    achternaam = " ".join(x for x in [naam.get("voorvoegsel"), naam["geslachtsnaam"]] if x)
    users.append({
        "username": bsn,
        "enabled": True,
        "emailVerified": True,
        "firstName": naam.get("voornamen", ""),
        "lastName": achternaam,
        "email": f"{bsn}@inwoner.voorbeeldstad.example",
        "attributes": {"bsn": [bsn]},
        "credentials": [{"type": "password", "value": "${DIGID_SIM_WACHTWOORD}", "temporary": False}],
    })

def attr_mapper(naam, attribuut, claim):
    return {
        "name": naam, "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-attribute-mapper",
        "config": {"user.attribute": attribuut, "claim.name": claim, "jsonType.label": "String",
                   "id.token.claim": "true", "access.token.claim": "true", "userinfo.token.claim": "true",
                   "introspection.token.claim": "true"},
    }

realm = {
    "realm": "voorbeeldstad",
    "displayName": "DigiD-simulatie Gemeente Voorbeeldstad",
    "displayNameHtml": "<b>DigiD-simulatie</b> Gemeente Voorbeeldstad (alleen fictieve testpersonen)",
    "enabled": True,
    "sslRequired": "none",
    "registrationAllowed": False,
    "loginWithEmailAllowed": False,
    "internationalizationEnabled": True,
    "supportedLocales": ["nl", "en"],
    "defaultLocale": "nl",
    "accessTokenLifespan": 900,
    "components": {
        "org.keycloak.userprofile.UserProfileProvider": [{
            "providerId": "declarative-user-profile",
            "subComponents": {},
            "config": {"kc.user.profile.config": [json.dumps(user_profile)]},
        }]
    },
    "clients": [
        {
            "clientId": "mijnservices",
            "name": "MijnServices (inwonersportaal)",
            "enabled": True,
            "publicClient": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "redirectUris": ["http://localhost:*", "http://127.0.0.1:*"],
            "webOrigins": ["+"],
            "attributes": {"pkce.code.challenge.method": "S256"},
            "protocolMappers": [
                attr_mapper("bsn", "bsn", "bsn"),
                {
                    "name": "betrouwbaarheidsniveau", "protocol": "openid-connect",
                    "protocolMapper": "oidc-hardcoded-claim-mapper",
                    "config": {"claim.name": "loa", "claim.value": "urn:etoegang:core:assurance-class:loa2plus",
                               "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "true",
                               "userinfo.token.claim": "true"},
                },
                {
                    "name": "audience-burgerportaal", "protocol": "openid-connect",
                    "protocolMapper": "oidc-audience-mapper",
                    "config": {"included.client.audience": "burgerportaal", "id.token.claim": "false", "access.token.claim": "true"},
                },
            ],
        },
        {
            "clientId": "burgerportaal",
            "name": "Burgerportaal (plug-in)",
            "enabled": True,
            "publicClient": False,
            "clientAuthenticatorType": "client-secret",
            "secret": "${KEYCLOAK_PORTAAL_CLIENT_SECRET}",
            "serviceAccountsEnabled": True,
            "standardFlowEnabled": False,
            "directAccessGrantsEnabled": False,
        },
    ],
    "users": users,
}

out = ROOT / "config/keycloak/voorbeeldstad-realm.json"
out.write_text(json.dumps(realm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"geschreven: {out}")
