"""Richt Keycloak in voor GZAC (idempotent): realmrollen, clients gzac-console en gzac-m2m, testgebruikers."""
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

ROLES = ["ROLE_USER", "ROLE_ADMIN", "ROLE_DEVELOPER"]
for role in ROLES:
    call("POST", f"{R}/roles", json={"name": role})

def client(cid):
    c = call("GET", f"{R}/clients", params={"clientId": cid})
    return c[0] if c else None
G = f"https://gzac.{D}"
if not client("gzac-console"):
    call("POST", f"{R}/clients", json={
        "clientId": "gzac-console", "name": "GZAC", "publicClient": True, "standardFlowEnabled": True,
        "directAccessGrantsEnabled": True, "rootUrl": G, "baseUrl": "/", "redirectUris": [f"{G}/*"],
        "webOrigins": [G], "attributes": {"post.logout.redirect.uris": f"{G}/*", "pkce.code.challenge.method": "S256"}})
# Direct grant nodig voor de rechtenwachter (scripts/gzac_permissions_watch.py)
call("PUT", f"{R}/clients/{client('gzac-console')['id']}", json={**client("gzac-console"), "directAccessGrantsEnabled": True})
if not client("gzac-m2m"):
    call("POST", f"{R}/clients", json={
        "clientId": "gzac-m2m", "name": "GZAC backend", "publicClient": False, "secret": os.environ["GZAC_M2M_SECRET"],
        "standardFlowEnabled": False, "serviceAccountsEnabled": True, "directAccessGrantsEnabled": False})
m2m = client("gzac-m2m")
sa = call("GET", f"{R}/clients/{m2m['id']}/service-account-user")
rm = client("realm-management")
want = ["view-users", "query-users", "query-groups", "view-realm", "query-clients", "query-realms", "view-clients", "manage-users"]
avail = {r["name"]: r for r in call("GET", f"{R}/clients/{rm['id']}/roles")}
call("POST", f"{R}/users/{sa['id']}/role-mappings/clients/{rm['id']}", json=[avail[n] for n in want])

USERS = [("behandelaar", "Jasmijn", "de Wit", ["ROLE_USER"]),
         ("beheerder", "Bea", "Beheer", ROLES)]
for u, f, l, roles in USERS:
    found = call("GET", f"{R}/users", params={"username": u, "exact": "true"})
    if not found:
        call("POST", f"{R}/users", json={"username": u, "enabled": True, "email": f"{u}@demogemeente.local", "emailVerified": True,
                                         "firstName": f, "lastName": l,
                                         "credentials": [{"type": "password", "value": PW, "temporary": False}]})
        found = call("GET", f"{R}/users", params={"username": u, "exact": "true"})
    uid = found[0]["id"]
    call("POST", f"{R}/users/{uid}/role-mappings/realm", json=[call("GET", f"{R}/roles/{n}") for n in roles])
print("keycloak gzac ok")
