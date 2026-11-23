"""Keycloak voor de inwonerportalen (idempotent).
NL Portal: public client 'nl-portal' voor de browser en confidential client 'nl-portal-m2m' die het token
omwisselt (standard token exchange v2) voor een token met het BSN als claim aanvrager.bsn.
ZaakChat: confidential client voor de inlogkoppeling.
Open Inwoner en de MijnOverheid-demo: gebruiken de nep-DigiD-client 'digid'; hier komen alleen de redirect-URI's erbij."""
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
def attr_mapper(attr, claim):
    return {"name": attr, "protocol": "openid-connect", "protocolMapper": "oidc-usermodel-attribute-mapper",
            "config": {"user.attribute": attr, "claim.name": claim, "jsonType.label": "String", "id.token.claim": "false",
                       "access.token.claim": "true", "userinfo.token.claim": "false", "introspection.token.claim": "true"}}
def audience(name):
    return {"name": "m2m-audience", "protocol": "openid-connect", "protocolMapper": "oidc-audience-mapper",
            "config": {"included.client.audience": name, "access.token.claim": "true", "id.token.claim": "false",
                       "introspection.token.claim": "true"}}
def upsert_client(body):
    found = call("GET", f"{R}/clients", params={"clientId": body["clientId"]})
    if not found:
        call("POST", f"{R}/clients", json=body)
        return call("GET", f"{R}/clients", params={"clientId": body["clientId"]})[0]
    c = found[0]; mappers = body.pop("protocolMappers", [])
    call("PUT", f"{R}/clients/{c['id']}", json={**c, **body, "attributes": {**c.get("attributes", {}), **body.get("attributes", {})}})
    have = {m["name"] for m in call("GET", f"{R}/clients/{c['id']}/protocol-mappers/models")}
    for m in mappers:
        if m["name"] not in have: call("POST", f"{R}/clients/{c['id']}/protocol-mappers/models", json=m)
    return c

# Client scope 'aanvrager': BSN en KVK als geneste claim, alleen op de m2m-client (nooit in de browser)
scopes = {s["name"]: s for s in call("GET", f"{R}/client-scopes")}
if "aanvrager" not in scopes:
    call("POST", f"{R}/client-scopes", json={"name": "aanvrager", "protocol": "openid-connect",
         "attributes": {"include.in.token.scope": "false", "display.on.consent.screen": "false"},
         "protocolMappers": [attr_mapper("bsn", "aanvrager.bsn"), attr_mapper("kvk", "aanvrager.kvk")]})
    scopes = {s["name"]: s for s in call("GET", f"{R}/client-scopes")}

P = f"https://portaal.{D}"; PO = f"https://portaal-og.{D}"  # tweede NL Portal, op OneGround
upsert_client({"clientId": "nl-portal", "name": "NL Portal (inwoner)", "publicClient": True,
    "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
    "redirectUris": [f"{P}/*", f"{PO}/*"], "webOrigins": [P, PO],
    "attributes": {"post.logout.redirect.uris": f"{P}/*##{PO}/*", "pkce.code.challenge.method": "S256"},
    "protocolMappers": [audience("nl-portal-m2m")]})
m2m = upsert_client({"clientId": "nl-portal-m2m", "name": "NL Portal backend", "publicClient": False,
    "secret": os.environ["NLP_M2M_SECRET"], "serviceAccountsEnabled": True, "standardFlowEnabled": False,
    "directAccessGrantsEnabled": False, "attributes": {"standard.token.exchange.enabled": "true"},
    "protocolMappers": [audience("nl-portal-m2m")]})
call("PUT", f"{R}/clients/{m2m['id']}/default-client-scopes/{scopes['aanvrager']['id']}")

# Mijn Demodam (OpenEvents): publieke client met PKCE; het token draagt rol=inwoner en het BSN,
# zodat de regels in de OpenEvents-profielen werken (actor = https://id.example.nl/{gebruikersnaam})
E = f"https://events.{D}"
upsert_client({"clientId": "mijn-demodam", "name": "Mijn Demodam (OpenEvents)", "publicClient": True,
    "standardFlowEnabled": True, "directAccessGrantsEnabled": False,
    "redirectUris": [f"{E}/mijnoverheid", f"{E}/mijnoverheid/"], "webOrigins": [E],
    "attributes": {"post.logout.redirect.uris": f"{E}/*", "pkce.code.challenge.method": "S256"},
    "protocolMappers": [
        {"name": "rol", "protocol": "openid-connect", "protocolMapper": "oidc-hardcoded-claim-mapper",
         "config": {"claim.name": "rol", "claim.value": "inwoner", "jsonType.label": "String",
                    "access.token.claim": "true", "id.token.claim": "false", "userinfo.token.claim": "false"}},
        attr_mapper("bsn", "bsn")]})

# ZaakChat: inwoners en medewerkers loggen in via de koppeling, die een ZaakChat-token afgeeft voor hun e-mailadres
Z = f"https://zaakchat.{D}"
upsert_client({"clientId": "zaakchat", "name": "ZaakChat", "publicClient": False, "secret": os.environ["ZAAKCHAT_OIDC_SECRET"],
    "standardFlowEnabled": True, "directAccessGrantsEnabled": False, "redirectUris": [f"{Z}/koppeling/*"], "webOrigins": [Z],
    "attributes": {"post.logout.redirect.uris": f"{Z}/*"}})

# Open Inwoner logt in via dezelfde nep-DigiD-client als Open Formulieren
dig = call("GET", f"{R}/clients", params={"clientId": "digid"})[0]
want = [f"https://formulieren.{D}/*", f"https://inwoner.{D}/*", f"https://mijnoverheid.{D}/*"]
if set(want) - set(dig.get("redirectUris", [])):
    dig["redirectUris"] = sorted(set(dig.get("redirectUris", [])) | set(want))
    dig.setdefault("attributes", {})["post.logout.redirect.uris"] = "+"
    call("PUT", f"{R}/clients/{dig['id']}", json=dig)
print("keycloak portalen ok")
