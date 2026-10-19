"""Keycloak van OneGround (eigen instantie, alleen intern): realm OneGround met per ZGW-client een confidential client
met serviceaccount en een vaste claim 'rsin' (de tenant). Hetzelfde als OneGround's eigen KeycloakSetup. Idempotent.
Clients in OG_CLIENTS als client_id=geheim,client_id=geheim."""
import os, sys, requests
K = os.environ.get("OG_KEYCLOAK", "http://og-keycloak:8080"); R = f"{K}/admin/realms/OneGround"; RSIN = "002220647"
tok = requests.post(f"{K}/realms/master/protocol/openid-connect/token", data={"client_id": "admin-cli", "username": "admin",
      "password": os.environ["OG_KC_ADMIN_PASSWORD"], "grant_type": "password"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
def call(m, url, ok=(200, 201, 204, 409), **kw):
    r = requests.request(m, url, headers=H, **kw)
    if r.status_code not in ok: print(m, url, r.status_code, r.text[:300]); sys.exit(1)
    return r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else None
call("POST", f"{K}/admin/realms", json={"realm": "OneGround", "enabled": True, "bruteForceProtected": True})
for pair in os.environ["OG_CLIENTS"].split(","):
    cid, secret = pair.split("=", 1)
    found = call("GET", f"{R}/clients", params={"clientId": cid})
    body = {"clientId": cid, "enabled": True, "publicClient": False, "clientAuthenticatorType": "client-secret", "secret": secret,
            "serviceAccountsEnabled": True, "standardFlowEnabled": False, "directAccessGrantsEnabled": False}
    if not found:
        call("POST", f"{R}/clients", json={**body, "protocolMappers": [{"name": "rsin", "protocol": "openid-connect",
             "protocolMapper": "oidc-hardcoded-claim-mapper", "config": {"claim.name": "rsin", "claim.value": RSIN,
             "jsonType.label": "String", "id.token.claim": "true", "access.token.claim": "true", "userinfo.token.claim": "true"}}]})
    else:
        call("PUT", f"{R}/clients/{found[0]['id']}", json={**found[0], **body})
print("keycloak oneground ok")
