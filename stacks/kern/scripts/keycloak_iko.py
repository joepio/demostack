"""Keycloak voor IKO (idempotent): confidential client 'iko'. Het beheerscherm leest de realmrollen uit de
ID-token-claim 'roles' (ROLE_ADMIN geeft toegang); de API leest resource_access.iko.roles met audience 'iko'.
Account 'demo' krijgt beide."""
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

I = f"https://iko.{D}"
if not call("GET", f"{R}/clients", params={"clientId": "iko"}):
    call("POST", f"{R}/clients", json={"clientId": "iko", "name": "IKO (klant- en objectbeeld)", "publicClient": False,
         "secret": os.environ["IKO_OIDC_SECRET"], "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
         "serviceAccountsEnabled": True, "redirectUris": [f"{I}/*"], "webOrigins": [I],
         "attributes": {"post.logout.redirect.uris": f"{I}/*"},
         "protocolMappers": [
             {"name": "roles", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-realm-role-mapper",
              "config": {"claim.name": "roles", "multivalued": "true", "jsonType.label": "String", "id.token.claim": "true",
                         "access.token.claim": "false", "userinfo.token.claim": "true"}},
             {"name": "audience", "protocol": "openid-connect", "protocolMapper": "oidc-audience-mapper",
              "config": {"included.client.audience": "iko", "access.token.claim": "true", "id.token.claim": "false"}}]})
c = call("GET", f"{R}/clients", params={"clientId": "iko"})[0]
call("POST", f"{R}/clients/{c['id']}/roles", json={"name": "ROLE_ADMIN"})
role = call("GET", f"{R}/clients/{c['id']}/roles/ROLE_ADMIN")
u = call("GET", f"{R}/users", params={"username": "demo", "exact": "true"})
if u:
    call("POST", f"{R}/users/{u[0]['id']}/role-mappings/clients/{c['id']}", json=[role])
sa = call("GET", f"{R}/clients/{c['id']}/service-account-user")
call("POST", f"{R}/users/{sa['id']}/role-mappings/clients/{c['id']}", json=[role])
print("keycloak iko ok")
