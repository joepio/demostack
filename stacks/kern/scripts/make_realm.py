"""Genereert de Keycloak-realm 'demogemeente' met client 'kiss' en testmedewerkers."""
import json, os, sys
B, PW, SECRET = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"], os.environ["KISS_OIDC_SECRET"]
ROLES = ["Klantcontactmedewerker", "Redacteur", "Beheerder", "Kennisbank"]
users = [
    ("kcc", "Kim", "Contact", ["Klantcontactmedewerker", "Kennisbank"]),
    ("redacteur", "Rik", "Redacteur", ["Klantcontactmedewerker", "Redacteur", "Kennisbank"]),
    ("beheerder", "Bea", "Beheer", ROLES),
]
realm = {
    "realm": "demogemeente", "enabled": True, "displayName": "Demogemeente", "sslRequired": "external",
    "loginWithEmailAllowed": True, "internationalizationEnabled": True, "supportedLocales": ["nl", "en"], "defaultLocale": "nl",
    "roles": {"client": {"kiss": [{"name": r} for r in ROLES]}},
    "clients": [{
        "clientId": "kiss", "name": "KISS", "enabled": True, "protocol": "openid-connect", "publicClient": False,
        "clientAuthenticatorType": "client-secret", "secret": SECRET, "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False, "rootUrl": f"https://kiss.{B}", "baseUrl": "/",
        "redirectUris": [f"https://kiss.{B}/*"], "webOrigins": [f"https://kiss.{B}"],
        "attributes": {"post.logout.redirect.uris": f"https://kiss.{B}/*", "pkce.code.challenge.method": "S256"},
        "protocolMappers": [{
            "name": "roles", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-client-role-mapper",
            "config": {"usermodel.clientRoleMapping.clientId": "kiss", "claim.name": "roles", "multivalued": "true",
                       "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "true",
                       "userinfo.token.claim": "true"}}],
    }],
    "users": [{
        "username": u, "enabled": True, "email": f"{u}@demogemeente.local", "emailVerified": True,
        "firstName": f, "lastName": l, "credentials": [{"type": "password", "value": PW, "temporary": False}],
        "clientRoles": {"kiss": roles}} for u, f, l, roles in users],
}
json.dump(realm, sys.stdout, indent=2)
