"""Richt Keycloak in voor ZAC en PABC (idempotent): clients, functionele rollen, groepen en testgebruikers."""
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
def client(cid):
    c = call("GET", f"{R}/clients", params={"clientId": cid}); return c[0] if c else None
Z = f"https://zac.{D}"
if not client("zac"):
    call("POST", f"{R}/clients", json={
        "clientId": "zac", "name": "ZAC", "publicClient": False, "secret": os.environ["ZAC_OIDC_SECRET"],
        "standardFlowEnabled": True, "directAccessGrantsEnabled": False, "rootUrl": Z, "baseUrl": "/",
        "redirectUris": [f"{Z}/*"], "webOrigins": [Z],
        "attributes": {"post.logout.redirect.uris": f"{Z}/*", "pkce.code.challenge.method": "S256"},
        "protocolMappers": [
            {"name": "groups", "protocol": "openid-connect", "protocolMapper": "oidc-group-membership-mapper",
             "config": {"claim.name": "group_membership", "full.path": "false", "id.token.claim": "true",
                        "access.token.claim": "true", "userinfo.token.claim": "true"}}]})
P = f"https://pabc.{D}"
if not client("pabc"):
    call("POST", f"{R}/clients", json={
        "clientId": "pabc", "name": "PABC", "publicClient": False, "secret": os.environ["PABC_OIDC_SECRET"],
        "standardFlowEnabled": True, "rootUrl": P, "redirectUris": [f"{P}/*"], "webOrigins": [P],
        "protocolMappers": [{"name": "clientRole", "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-client-role-mapper",
            "config": {"usermodel.clientRoleMapping.clientId": "pabc", "claim.name": "roles", "multivalued": "true",
                       "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "true", "userinfo.token.claim": "true"}}]})
    call("POST", f"{R}/clients/{client('pabc')['id']}/roles", json={"name": "administrator"})
rm = client("realm-management"); acc = client("account")
rm_roles = {r["name"]: r for r in call("GET", f"{R}/clients/{rm['id']}/roles")}
acc_roles = {r["name"]: r for r in call("GET", f"{R}/clients/{acc['id']}/roles")}
for cid, secret, rmw in [("zac-admin-client", "ZAC_ADMIN_SECRET", ["view-users", "query-users", "query-groups"]),
                         ("pabc-admin-client", "PABC_ADMIN_SECRET", ["view-users", "view-realm", "query-users", "query-groups"])]:
    if not client(cid):
        call("POST", f"{R}/clients", json={"clientId": cid, "publicClient": False, "secret": os.environ[secret],
                                            "standardFlowEnabled": False, "serviceAccountsEnabled": True})
    sa = call("GET", f"{R}/clients/{client(cid)['id']}/service-account-user")
    call("POST", f"{R}/users/{sa['id']}/role-mappings/clients/{rm['id']}", json=[rm_roles[n] for n in rmw])
    if "view-groups" in acc_roles:
        call("POST", f"{R}/users/{sa['id']}/role-mappings/clients/{acc['id']}", json=[acc_roles["view-groups"]])

# Functionele rollen (realm-rollen) en groepen; PABC vertaalt ze naar ZAC-rollen
FROLES = {"behandelaar_openbare_ruimte": "team-meldingen", "coordinator_openbare_ruimte": "coordinatoren-openbare-ruimte",
          "beheerder_elk_domein": "zac-beheerders"}
for role, group in FROLES.items():
    call("POST", f"{R}/roles", json={"name": role})
    if not [g for g in call("GET", f"{R}/groups", params={"search": group, "exact": "true"}) if g["name"] == group]:
        call("POST", f"{R}/groups", json={"name": group})
    g = [g for g in call("GET", f"{R}/groups", params={"search": group, "exact": "true"}) if g["name"] == group][0]
    call("POST", f"{R}/groups/{g['id']}/role-mappings/realm", json=[call("GET", f"{R}/roles/{role}")])

def ensure_user(u, f, l, groups, pabc_admin=False):
    found = call("GET", f"{R}/users", params={"username": u, "exact": "true"})
    if not found:
        call("POST", f"{R}/users", json={"username": u, "enabled": True, "email": f"{u}@demogemeente.local", "emailVerified": True,
             "firstName": f, "lastName": l, "credentials": [{"type": "password", "value": PW, "temporary": False}]})
        found = call("GET", f"{R}/users", params={"username": u, "exact": "true"})
    uid = found[0]["id"]
    for group in groups:
        g = [g for g in call("GET", f"{R}/groups", params={"search": group, "exact": "true"}) if g["name"] == group][0]
        call("PUT", f"{R}/users/{uid}/groups/{g['id']}")
    if pabc_admin:
        pc = client("pabc"); role = call("GET", f"{R}/clients/{pc['id']}/roles/administrator")
        call("POST", f"{R}/users/{uid}/role-mappings/clients/{pc['id']}", json=[role])
ensure_user("behandelaar", "Jasmijn", "de Wit", ["team-meldingen"])
ensure_user("m.bakker", "Mehmet", "Bakker", ["team-meldingen"])
ensure_user("coordinator", "Chris", "Coördinator", ["coordinatoren-openbare-ruimte", "team-meldingen"])
ensure_user("beheerder", "Bea", "Beheer", ["zac-beheerders"], pabc_admin=True)
print("keycloak zac ok")
