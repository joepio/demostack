"""MijnGesprekken-demo op DemoStack: stub-IDP en stub-Autorisaties voor de Gesprekken API (intern), plus de
medewerkerconsole en de regiepagina (publiek). Alleen standaardbibliotheek plus PyJWT en requests."""
import base64, json, os, re, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import jwt, requests
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

E = os.environ
ISS = E.get("ISSUER", "http://mg-app:8080/idp")
RSIN = E.get("RSIN", "002220647")
GRC = E.get("GRC_API", "http://mg-grc:5000/api/v1").rstrip("/")
OK_API = E.get("OK_API", "").rstrip("/")
OK_TOKEN = E.get("OK_TOKEN", "")
OIP_URL = E.get("OIP_URL", "")
OK_ADMIN_URL = E.get("OK_ADMIN_URL", "")
ACTOR = E.get("ONTVANGER_ACTOR", "")
HERE = os.path.dirname(os.path.abspath(__file__))

KEYFILE = "/data/idp-key.pem"
os.makedirs("/data", exist_ok=True)
if os.path.exists(KEYFILE):
    KEY = serialization.load_pem_private_key(open(KEYFILE, "rb").read(), None)
else:
    KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    open(KEYFILE, "wb").write(KEY.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                                serialization.NoEncryption()))
KID = "mgdemo-1"
_pub = KEY.public_key().public_numbers()
b64 = lambda n: base64.urlsafe_b64encode(n.to_bytes((n.bit_length() + 7) // 8, "big")).rstrip(b"=").decode()
# Korte ES256-tokens: zgw-consumers bewaart een header van hoogstens 255 tekens
from cryptography.hazmat.primitives.asymmetric import ec
ECFILE = "/data/idp-ec.pem"
if os.path.exists(ECFILE):
    EC = serialization.load_pem_private_key(open(ECFILE, "rb").read(), None)
else:
    EC = ec.generate_private_key(ec.SECP256R1())
    open(ECFILE, "wb").write(EC.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                              serialization.NoEncryption()))
_ecp = EC.public_key().public_numbers()
b64f = lambda n: base64.urlsafe_b64encode(n.to_bytes(32, "big")).rstrip(b"=").decode()
JWKS = {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": KID, "n": b64(_pub.n), "e": b64(_pub.e)},
                 {"kty": "EC", "use": "sig", "alg": "ES256", "kid": "e", "crv": "P-256", "x": b64f(_ecp.x), "y": b64f(_ecp.y)}]}
TOKEN_ISS = E.get("TOKEN_ISSUER", "i")


def short_token(client_id, lifetime):
    claims = {"iss": TOKEN_ISS, "aud": "account", "client_id": client_id, "rsin": RSIN, "exp": int(time.time()) + lifetime}
    return jwt.encode(claims, EC, algorithm="ES256", headers={"kid": "e", "typ": None})


def token(client_id, lifetime=3600):
    now = int(time.time())
    claims = {"iss": TOKEN_ISS, "aud": "account", "sub": client_id, "azp": client_id, "client_id": client_id, "rsin": RSIN,
              "iat": now, "nbf": now, "exp": now + lifetime, "jti": str(uuid.uuid4()), "typ": "Bearer"}
    return jwt.encode(claims, KEY, algorithm="RS256", headers={"kid": KID})


_tok = {"v": None, "exp": 0}
def grc_headers():
    if time.time() > _tok["exp"] - 60:
        _tok["v"], _tok["exp"] = token("mgdemo-console"), time.time() + 3600
    return {"Authorization": f"Bearer {_tok['v']}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}


def ok_headers():
    return {"Authorization": f"Token {OK_TOKEN}"}


def uuid_of(url):
    return url.rstrip("/").rsplit("/", 1)[-1] if url else None


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "mgdemo"

    def log_message(self, fmt, *args):
        if "/health" not in self.path:
            print(self.command, self.path.split("?")[0], *args[1:2], flush=True)

    def send(self, code, body=b"", ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    # ---------- routes ----------
    def do_GET(self):
        u = urlparse(self.path); p = u.path; q = parse_qs(u.query)
        if p == "/health":
            return self.send(200, {"ok": True})
        # IDP (intern)
        if p == "/idp/.well-known/openid-configuration":
            return self.send(200, {"issuer": ISS, "jwks_uri": f"{ISS}/certs", "token_endpoint": f"{ISS}/token",
                                   "authorization_endpoint": f"{ISS}/auth", "response_types_supported": ["token"],
                                   "subject_types_supported": ["public"], "grant_types_supported": ["client_credentials"],
                                   "id_token_signing_alg_values_supported": ["RS256"]})
        if p == "/idp/certs":
            return self.send(200, JWKS)
        if p == "/idp/longtoken":  # intern: token met lange looptijd voor Open Inwoner
            return self.send(200, {"token": short_token(q.get("client_id", ["oip"])[0], 3600 * 24 * 60)})
        # Autorisaties (intern): elke client mag alles
        if p.endswith("/applicaties/consumer"):
            cid = q.get("clientId", [""])[0]
            return self.send(200, {"url": f"http://mg-app:8080/ac/api/v1/applicaties/{uuid.uuid5(uuid.NAMESPACE_URL, cid)}",
                                   "clientIds": [cid], "label": cid, "heeftAlleAutorisaties": True, "autorisaties": []})
        # Publiek: console en regiepagina
        if p in ("/", ""):
            return self.send(302, b"", headers={"Location": "/regie/"})
        if p in ("/regie", "/regie/"):
            html = open(os.path.join(HERE, "regie.html")).read().replace("{{OIP_URL}}", OIP_URL)
            return self.send(200, html, "text/html; charset=utf-8")
        if p in ("/medewerker", "/medewerker/"):
            html = open(os.path.join(HERE, "medewerker.html")).read().replace("{{OK_ADMIN_URL}}", OK_ADMIN_URL)
            return self.send(200, html, "text/html; charset=utf-8")
        if p == "/api/gesprekken":
            r = requests.get(f"{GRC}/gesprekken", params={"pageSize": 50}, headers=grc_headers(), timeout=15)
            return self.send(r.status_code, r.content)
        m = re.fullmatch(r"/api/gesprekken/([0-9a-f-]{36})", p)
        if m:
            r = requests.get(f"{GRC}/gesprekken/{m[1]}", headers=grc_headers(), timeout=15)
            return self.send(r.status_code, r.content)
        m = re.fullmatch(r"/api/bestand/([0-9a-f-]{36})", p)
        if m:
            r = requests.get(f"{GRC}/bestanden/{m[1]}", headers=grc_headers(), timeout=15)
            d = r.json() if r.ok else {}
            if d.get("downloadUrl"):
                return self.send(302, b"", headers={"Location": d["downloadUrl"]})
            return self.send(404, {"fout": "bestand niet beschikbaar", "status": d.get("status")})
        if p == "/api/klantcontacten":
            if not OK_API:
                return self.send(200, {"results": []})
            r = requests.get(f"{OK_API}/klantcontacten", params={"pageSize": 20, "expand": "hadBetrokkenen,gingOverOnderwerpobjecten"},
                             headers=ok_headers(), timeout=15)
            return self.send(r.status_code, r.content)
        if p == "/api/events":
            return self.events(self.headers.get("Last-Event-ID") or q.get("vanaf", ["0"])[0])
        return self.send(404, {"fout": "niet gevonden"})

    def do_POST(self):
        p = urlparse(self.path).path
        if p == "/idp/token":
            form = parse_qs(self.body().decode())
            cid = form.get("client_id", [""])[0]
            if not cid and self.headers.get("Authorization", "").startswith("Basic "):
                cid = base64.b64decode(self.headers["Authorization"][6:]).decode().split(":", 1)[0]
            from urllib.parse import unquote
            cid = unquote(cid or "onbekend")
            return self.send(200, {"access_token": token(cid), "token_type": "Bearer", "expires_in": 3600})
        if p == "/api/antwoord":
            d = json.loads(self.body() or b"{}")
            g = requests.get(f"{GRC}/gesprekken/{d['gesprek']}", headers=grc_headers(), timeout=15)
            if not g.ok:
                return self.send(g.status_code, g.content)
            gesprek = g.json()
            actoren = [x for x in gesprek.get("gespreksdeelnames", [])
                       if x.get("type") == "actor" and not x.get("momentEindeDeelname")]
            eigen = next((x for x in actoren if x.get("actor") == ACTOR), None) or next(
                (x for x in actoren if "automatisch" not in (x.get("naam") or "").lower()), None)
            verzender = {"gespreksdeelname": eigen["url"]} if eigen else {
                "nieuweDeelname": {"type": "actor", "actor": ACTOR, "naam": "Medewerker Demogemeente"}}
            r = requests.post(f"{GRC}/gespreksbijdragen", headers=grc_headers(), timeout=15, json={
                "gesprek": gesprek["url"], "tekstGespreksBijdrage": d["tekst"], "verzender": verzender, "bijlagen": []})
            return self.send(r.status_code, r.content)
        m = re.fullmatch(r"/api/gesprekken/([0-9a-f-]{36})/eindigen", p)
        if m:
            r = requests.post(f"{GRC}/gesprekken/{m[1]}/eindigen", headers=grc_headers(), timeout=30)
            return self.send(r.status_code, r.content)
        return self.send(404, {"fout": "niet gevonden"})

    def events(self, vanaf):
        h = {**grc_headers(), "Accept": "text/event-stream"}
        if vanaf:
            h["Last-Event-ID"] = vanaf
        try:
            up = requests.get(f"{GRC}/events", headers=h, stream=True, timeout=(10, 120))
        except requests.RequestException as e:
            return self.send(502, {"fout": str(e)})
        if up.status_code == 410:
            up.close(); h.pop("Last-Event-ID", None)
            up = requests.get(f"{GRC}/events", headers=h, stream=True, timeout=(10, 120))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        try:
            for chunk in up.iter_content(chunk_size=None):
                self.wfile.write(chunk); self.wfile.flush()
        except Exception:
            pass
        finally:
            up.close()


if __name__ == "__main__":
    ThreadingHTTPServer.daemon_threads = True
    print("mgdemo op :8080", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8080), H).serve_forever()
