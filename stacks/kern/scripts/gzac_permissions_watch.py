"""Wachter voor GZAC: de demo-image zet bij elke start de rechten terug. Elke minuut controleren we of ROLE_USER
dossierrechten heeft; zo niet, dan kopiëren we die van ROLE_ADMIN. Alleen standaardbibliotheek."""
import json, os, time, urllib.parse, urllib.request
D, PW = os.environ["BASE_DOMAIN"], os.environ["ADMIN_PASSWORD"]
KC = f"https://keycloak.{D}/realms/demogemeente/protocol/openid-connect/token"
API = "http://gzac-backend:8080/api/management/v1/roles"

def req(url, data=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        body = resp.read()
        return json.loads(body) if body else None

while True:
    try:
        form = urllib.parse.urlencode({"client_id": "gzac-console", "grant_type": "password",
                                       "username": "beheerder", "password": PW}).encode()
        with urllib.request.urlopen(urllib.request.Request(KC, data=form), timeout=30) as resp:
            token = json.load(resp)["access_token"]
        if not req(f"{API}/ROLE_USER/permissions", token=token):
            perms = req(f"{API}/ROLE_ADMIN/permissions", token=token)
            for p in perms:
                p.pop("role", None)
            req(f"{API}/ROLE_USER/permissions", data=json.dumps(perms).encode(), token=token, method="PUT")
            print("ROLE_USER-rechten hersteld", flush=True)
    except Exception as e:  # backend nog niet klaar of Keycloak even weg: volgende ronde opnieuw
        print("wacht:", str(e)[:120], flush=True)
    time.sleep(60)
