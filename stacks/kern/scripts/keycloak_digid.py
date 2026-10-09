"""Nep-DigiD in Keycloak (idempotent): client 'digid' die het BSN als claim meegeeft, en testinwoners uit de BRP-testset."""
import os, sys, requests
D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
K = f"https://keycloak.{D}"; R = f"{K}/admin/realms/demogemeente"
tok = requests.post(f"{K}/realms/master/protocol/openid-connect/token", data={
    "client_id": "admin-cli", "username": "admin", "password": PW, "grant_type": "password"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
def call(m, url, ok=(200, 201, 204, 409), **kw):
    r = requests.request(m, url, headers=H, **kw)
    if r.status_code not in ok: print(m, url, r.status_code, r.text[:400]); sys.exit(1)
    return r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else None
# Keycloak 26 bewaart alleen gedeclareerde attributen; 'bsn' toestaan
prof = call("GET", f"{R}/users/profile")
if prof.get("unmanagedAttributePolicy") != "ENABLED":
    prof["unmanagedAttributePolicy"] = "ENABLED"; call("PUT", f"{R}/users/profile", json=prof)
c = call("GET", f"{R}/clients", params={"clientId": "digid"})
if not c:
    call("POST", f"{R}/clients", json={"clientId": "digid", "name": "DigiD (demo)", "publicClient": False,
         "secret": os.environ["DIGID_OIDC_SECRET"], "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
         "redirectUris": [f"https://formulieren.{D}/*"], "webOrigins": ["+"],
         "protocolMappers": [{"name": "bsn", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-attribute-mapper",
             "config": {"user.attribute": "bsn", "claim.name": "bsn", "jsonType.label": "String", "id.token.claim": "true",
                        "access.token.claim": "true", "userinfo.token.claim": "true"}}]})
INWONERS = [("suzanne", "Suzanne", "Moulin", "999993653"), ("lukas", "Lukas", "Klamer", "999991723"),
            ("merel", "Merel", "Kooyman", "999993847")]
for u, f, l, bsn in INWONERS:
    found = call("GET", f"{R}/users", params={"username": u, "exact": "true"})
    body = {"username": u, "enabled": True, "email": f"{u}@example.com", "emailVerified": True,
            "firstName": f, "lastName": l, "attributes": {"bsn": [bsn]}}
    if not found:
        call("POST", f"{R}/users", json={**body, "credentials": [{"type": "password", "value": PW, "temporary": False}]})
    else:
        call("PUT", f"{R}/users/{found[0]['id']}", json={**found[0], "attributes": {"bsn": [bsn]}})
print("keycloak digid ok")
