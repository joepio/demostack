"""Single sign-on (idempotent): client 'beheer' voor de beheerschermen van de Django-apps, langere sessies,
groep 'beheerders' (superuser in de beheerschermen) en één account 'demo' dat alle rollen heeft."""
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
def group(name):
    g = [g for g in call("GET", f"{R}/groups", params={"search": name, "exact": "true"}) if g["name"] == name]
    if not g:
        call("POST", f"{R}/groups", json={"name": name}); return group(name)
    return g[0]

# Langere sessies: een werkdag zonder opnieuw inloggen, met 'onthoud mij' een week
realm = call("GET", R)
realm.update({"ssoSessionIdleTimeout": 12 * 3600, "ssoSessionMaxLifespan": 7 * 86400, "rememberMe": True,
              "ssoSessionIdleTimeoutRememberMe": 7 * 86400, "ssoSessionMaxLifespanRememberMe": 7 * 86400})
call("PUT", R, json=realm)

HOSTS = ["zaken", "formulieren", "klant", "objecten", "objecttypen", "notificaties", "inwoner"]
redirects = [f"https://{h}.{D}/*" for h in HOSTS]
mapper = {"name": "groups", "protocol": "openid-connect", "protocolMapper": "oidc-group-membership-mapper",
          "config": {"claim.name": "groups", "full.path": "false", "id.token.claim": "true",
                     "access.token.claim": "true", "userinfo.token.claim": "true"}}
c = client("beheer")
if not c:
    call("POST", f"{R}/clients", json={"clientId": "beheer", "name": "Beheerschermen", "publicClient": False,
         "secret": os.environ["BEHEER_OIDC_SECRET"], "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
         "redirectUris": redirects, "webOrigins": ["+"], "attributes": {"post.logout.redirect.uris": "+"},
         "protocolMappers": [mapper]})
else:
    call("PUT", f"{R}/clients/{c['id']}", json={**c, "redirectUris": redirects})
beheerders = group("beheerders")

# Inloggen zonder wachtwoord voor de demo-accounts (services/demo-login): serviceaccount met de rol 'impersonation'
dl = {"clientId": "demo-login", "name": "Demo: inloggen zonder wachtwoord", "publicClient": False, "secret": os.environ["DEMO_LOGIN_SECRET"],
      "serviceAccountsEnabled": True, "standardFlowEnabled": False, "directAccessGrantsEnabled": False}
if not client("demo-login"):
    call("POST", f"{R}/clients", json=dl)
c_dl = client("demo-login"); rm = client("realm-management")
sa = call("GET", f"{R}/clients/{c_dl['id']}/service-account-user")
call("POST", f"{R}/users/{sa['id']}/role-mappings/clients/{rm['id']}",
     json=[call("GET", f"{R}/clients/{rm['id']}/roles/{n}") for n in ("impersonation", "view-users")])

# Welkomstpagina: public client die alleen toont wie er ingelogd is en wisselen van gebruiker mogelijk maakt
W = f"https://{D}"
welkom = {"clientId": "welkom", "name": "Welkomstpagina", "publicClient": True, "standardFlowEnabled": True,
          "directAccessGrantsEnabled": False, "redirectUris": [f"{W}/*"], "webOrigins": [W],
          "attributes": {"post.logout.redirect.uris": f"{W}/*", "pkce.code.challenge.method": "S256"}}
w = client("welkom")
if not w:
    call("POST", f"{R}/clients", json=welkom)
else:
    call("PUT", f"{R}/clients/{w['id']}", json={**w, **welkom, "attributes": {**w.get("attributes", {}), **welkom["attributes"]}})

# Eén account voor alles
u = call("GET", f"{R}/users", params={"username": "demo", "exact": "true"})
if not u:
    call("POST", f"{R}/users", json={"username": "demo", "enabled": True, "email": "demo@demogemeente.local", "emailVerified": True,
         "firstName": "Demo", "lastName": "Gebruiker", "credentials": [{"type": "password", "value": PW, "temporary": False}]})
    u = call("GET", f"{R}/users", params={"username": "demo", "exact": "true"})
uid = u[0]["id"]
for name in ["beheerders", "team-meldingen", "coordinatoren-openbare-ruimte", "zac-beheerders"]:
    call("PUT", f"{R}/users/{uid}/groups/{group(name)['id']}")
call("POST", f"{R}/users/{uid}/role-mappings/realm", json=[call("GET", f"{R}/roles/{n}") for n in ["ROLE_USER", "ROLE_ADMIN", "ROLE_DEVELOPER"]])
for cid, roles in [("kiss", ["Klantcontactmedewerker", "Redacteur", "Beheerder"]), ("pabc", ["administrator"])]:
    cl = client(cid)
    call("POST", f"{R}/users/{uid}/role-mappings/clients/{cl['id']}", json=[call("GET", f"{R}/clients/{cl['id']}/roles/{n}") for n in roles])
# De bestaande beheerder mag ook in de beheerschermen
b = call("GET", f"{R}/users", params={"username": "beheerder", "exact": "true"})
if b: call("PUT", f"{R}/users/{b[0]['id']}/groups/{beheerders['id']}")
print("keycloak sso ok")
