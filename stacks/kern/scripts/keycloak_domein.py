"""Zet alle client-URLs in realm 'demogemeente' om van OUD_DOMEIN naar BASE_DOMAIN (na een domeinwissel)."""
import json, os, sys, requests
OLD, NEW, PW = os.environ["OUD_DOMEIN"], os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
K = f"https://keycloak.{NEW}"; R = f"{K}/admin/realms/demogemeente"
tok = requests.post(f"{K}/realms/master/protocol/openid-connect/token", data={
    "client_id": "admin-cli", "username": "admin", "password": PW, "grant_type": "password"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
n = 0
for c in requests.get(f"{R}/clients", headers=H).json():
    raw = json.dumps(c)
    if OLD in raw:
        c2 = json.loads(raw.replace(OLD, NEW))
        r = requests.put(f"{R}/clients/{c['id']}", headers=H, json=c2)
        print(c["clientId"], r.status_code); n += 1
print("clients bijgewerkt:", n)
