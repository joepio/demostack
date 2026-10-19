"""Inloggen zonder wachtwoord, alleen voor de demo-accounts.

Draait achter keycloak.<domein>/demo-login, zodat de sessiecookies van Keycloak op het juiste domein landen.
Gebruikt de impersonatiefunctie van Keycloak met een serviceaccount (rol 'impersonation' in deze realm):
GET /demo-login?als=suzanne&terug=https://demostack.nl/ start een Keycloak-sessie als suzanne en stuurt terug.
Werkt alleen voor de accounts in DEMO_ACCOUNTS en alleen terug naar adressen onder BASE_DOMAIN.
"""
import os, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import requests

D = os.environ["BASE_DOMAIN"]
K = os.environ.get("KEYCLOAK_URL", f"https://keycloak.{D}")
R = f"{K}/admin/realms/demogemeente"
CLIENT, SECRET = "demo-login", os.environ["DEMO_LOGIN_SECRET"]
ACCOUNTS = set(os.environ.get("DEMO_ACCOUNTS", "").split(","))
http = requests.Session()


def toegestaan(url):
    u = urllib.parse.urlsplit(url)
    return u.scheme == "https" and (u.hostname == D or (u.hostname or "").endswith("." + D))


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path.split('&')[0]} {args[1] if len(args) > 1 else ''}", flush=True)

    def fout(self, code, tekst):
        body = tekst.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        als, terug = q.get("als", ""), q.get("terug", f"https://{D}/")
        if als not in ACCOUNTS:
            return self.fout(403, "Dit account kan niet zonder wachtwoord inloggen.")
        if not toegestaan(terug):
            return self.fout(400, "Ongeldig terug-adres.")
        try:
            tok = http.post(f"{K}/realms/demogemeente/protocol/openid-connect/token", timeout=15, data={
                "grant_type": "client_credentials", "client_id": CLIENT, "client_secret": SECRET}).json()["access_token"]
            H_ = {"Authorization": f"Bearer {tok}"}
            users = http.get(f"{R}/users", params={"username": als, "exact": "true"}, headers=H_, timeout=15).json()
            r = http.post(f"{R}/users/{users[0]['id']}/impersonation", headers=H_, timeout=15)
            r.raise_for_status()
        except Exception as e:
            print("mislukt:", type(e).__name__, str(e)[:200], flush=True)
            return self.fout(502, "Inloggen zonder wachtwoord lukt nu niet. Log gewoon in met het wachtwoord.")
        # De sessiecookies van Keycloak doorgeven aan de browser
        self.send_response(302)
        self.send_header("Location", terug)
        self.send_header("Cache-Control", "no-store")
        for c in r.raw.headers.getlist("Set-Cookie"):
            self.send_header("Set-Cookie", c)
        self.send_header("Content-Length", "0")
        self.end_headers()


if __name__ == "__main__":
    print("demo-login op :8080", flush=True)
    ThreadingHTTPServer(("", 8080), H).serve_forever()
