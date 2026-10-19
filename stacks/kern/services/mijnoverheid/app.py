"""Adapter voor de MijnOverheid-demo (VNG API Lab).

- Inloggen met nep-DigiD (Keycloak); de sessie bevat alleen BSN en naam, ondertekend met een geheim.
- MijnZaken (zaken/next) en MijnTaken (taken/next) komen uit Open Zaak en Objecten (TaakV2),
  gefilterd op het BSN van de ingelogde inwoner, aangevuld met de mockgegevens van het Rijk.
- MijnGegevens komt uit de BRP (mock), omgezet naar de partijvorm die de app verwacht.
- Alle andere API's van de app gaan ongewijzigd door naar de mockserver van het API Lab.
- De chatassistent werkt alleen als OPENROUTER_API_KEY gezet is.
"""
import base64, hashlib, hmac, html, json, mimetypes, os, secrets, time, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import jwt, requests

D = os.environ["BASE_DOMAIN"]
ORIGIN = f"https://mijnoverheid.{D}"
KC = f"https://keycloak.{D}/realms/demogemeente/protocol/openid-connect"
CLIENT, CLIENT_SECRET = "digid", os.environ["DIGID_OIDC_SECRET"]
SESSION_KEY = os.environ["MO_SESSION_SECRET"].encode()
ZGW_ID, ZGW_SECRET = "mijnoverheid", os.environ["MO_ZGW_SECRET"]
OZ = f"https://zaken.{D}"
OBJ = f"https://objecten.{D}/api/v2"
OBJ_TOKEN = os.environ["MO_OBJ_TOKEN"]
TAAK_OT = f"https://objecttypen.{D}/api/v2/objecttypes/{os.environ['TAAK_OT']}"
BRP = os.environ.get("BRP_URL", "http://personen-mock:5010/haalcentraal/api/brp/personen")
MOCK = os.environ.get("MOCK_BASE", "https://vng-interactie-mocks.fly.dev")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "deepseek/deepseek-chat")
STATIC = "/app/static"
GEMEENTE = "Demogemeente"
jwks = jwt.PyJWKClient(f"{KC}/certs")
http = requests.Session()


def sign(data: dict) -> str:
    raw = base64.urlsafe_b64encode(json.dumps(data).encode()).decode()
    mac = hmac.new(SESSION_KEY, raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{mac}"


def unsign(value: str):
    try:
        raw, mac = value.rsplit(".", 1)
        if not hmac.compare_digest(mac, hmac.new(SESSION_KEY, raw.encode(), hashlib.sha256).hexdigest()):
            return None
        data = json.loads(base64.urlsafe_b64decode(raw))
        return data if data.get("exp", 0) > time.time() else None
    except Exception:
        return None


def zgw_headers():
    t = jwt.encode({"iss": ZGW_ID, "iat": int(time.time()), "client_id": ZGW_ID, "user_id": ZGW_ID,
                    "user_representation": "MijnOverheid-demo"}, ZGW_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326"}


def oz_get(url, **params):
    r = http.get(url, headers=zgw_headers(), params=params, timeout=20)
    r.raise_for_status()
    return r.json()


# ---------- zaken ----------
def eigen_zaken(bsn):
    data = oz_get(f"{OZ}/zaken/api/v1/zaken", rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=bsn)
    return data.get("results", [])


def zaak_samenvatting(z):
    zt = oz_get(z["zaaktype"])
    return {"uuid": z["uuid"], "zaaknummer": z["identificatie"],
            "naam": f"{zt['omschrijving']}: {z['omschrijving']}" if z.get("omschrijving") else zt["omschrijving"],
            "status": "Gesloten" if z.get("einddatum") else "Open",
            "datumAanvraag": z.get("registratiedatum") or z.get("startdatum")}


def zaak_detail(z, bsn):
    out = zaak_samenvatting(z)
    statustypen = sorted(oz_get(f"{OZ}/catalogi/api/v1/statustypen", zaaktype=z["zaaktype"])["results"],
                         key=lambda s: s["volgnummer"])
    statussen = oz_get(f"{OZ}/zaken/api/v1/statussen", zaak=z["url"])["results"]
    bereikt = {s["statustype"]: s for s in statussen}
    huidig = oz_get(z["status"])["statustype"] if z.get("status") else None
    nr_huidig = next((s["volgnummer"] for s in statustypen if s["url"] == huidig), 0)
    stappen = []
    for st in statustypen:
        if st["volgnummer"] < nr_huidig or (st["url"] == huidig and z.get("einddatum")):
            status = "voltooid"
        elif st["url"] == huidig:
            status = "lopend"
        else:
            status = "gepland"
        toel = [bereikt[st["url"]]["statustoelichting"]] if st["url"] in bereikt and bereikt[st["url"]].get("statustoelichting") else []
        stappen.append({"nummer": st["volgnummer"], "titel": st.get("statustekst") or st["omschrijving"],
                        "status": status, "toelichting": toel})
    docs = []
    for zio in oz_get(f"{OZ}/zaken/api/v1/zaakinformatieobjecten", zaak=z["url"]):
        d = oz_get(zio["informatieobject"])
        if d.get("vertrouwelijkheidaanduiding") not in ("openbaar", "beperkt_openbaar", "intern", "zaakvertrouwelijk"):
            continue
        kb = max(1, int(d.get("bestandsomvang") or 0) // 1024)
        docs.append({"naam": d.get("titel") or d.get("bestandsnaam"), "type": (d.get("formaat") or "").split("/")[-1].upper() or "Bestand",
                     "grootte": f"{kb} kB", "datum": d.get("creatiedatum"), "bron": GEMEENTE})
    out.update({"statushistorie": stappen, "documenten": docs, "contactmomenten": []})
    taak = next((t for t in eigen_taken(bsn) if (t.get("koppeling") or {}).get("value") == z["uuid"]), None)
    if taak:
        out["openstaandeTaak"] = {"titel": taak["titel"], "deadlineText": "Zo snel mogelijk",
                                  "actieUrl": (taak.get("url") or {}).get("uri", ORIGIN)}
    return out


# ---------- taken ----------
def eigen_taken(bsn):
    r = http.get(f"{OBJ}/objects", headers={"Authorization": f"Token {OBJ_TOKEN}"}, timeout=20, params={
        "type": TAAK_OT, "data_attr": f"identificatie__value__exact__{bsn}"})
    r.raise_for_status()
    return [dict(o["record"]["data"], _uuid=o["uuid"]) for o in r.json()["results"]
            if o["record"]["data"].get("status") == "open"]


def taak_samenvatting(t):
    out = {"uuid": t["_uuid"], "titel": {"nl": t["titel"]}, "status": "open",
           "uitvoering": {"type": "url" if t.get("soort") == "url" else t.get("soort", "url"),
                          "canonicalUrl": (t.get("url") or {}).get("uri", ORIGIN)}}
    k = t.get("koppeling") or {}
    if k.get("registratie") == "zaak":
        out["context"] = {"urn": f"urn:nl:gemeenten:zaak:{k['value']}", "canonicalUrl": f"https://inwoner.{D}/cases/"}
    if t.get("verloopdatum"):
        out["deadline"] = t["verloopdatum"]
    return out


# ---------- gegevens (BRP) in de vorm van een Open Klant-partij, zoals de app die verwacht ----------
def gegevens_partij(bsn):
    r = http.post(BRP, timeout=20, json={"type": "RaadpleegMetBurgerservicenummer", "burgerservicenummer": [bsn],
                                          "fields": ["naam", "verblijfplaats"]})
    r.raise_for_status()
    p = (r.json().get("personen") or [{}])[0]
    adr = (p.get("verblijfplaats") or {}).get("verblijfadres") or {}
    adres = {"straatnaam": adr.get("officieleStraatnaam"), "huisnummer": adr.get("huisnummer"),
             "huisnummertoevoeging": adr.get("huisletter") or adr.get("huisnummertoevoeging"),
             "postcode": adr.get("postcode"), "stad": adr.get("woonplaats")}
    return {"volledigeNaam": (p.get("naam") or {}).get("volledigeNaam"), "bezoekadres": adres, "correspondentieadres": adres,
            "partijIdentificatoren": [{"partijIdentificator": {"codeSoortObjectId": "bsn", "objectId": bsn}}],
            "_expand": {"digitale_adressen": []}}


GEEN_BSN = """<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Inloggen als inwoner</title><style>body{{font:16px/1.5 system-ui,sans-serif;max-width:560px;margin:10vh auto;padding:0 16px;color:#1b1f27}}
a.b{{display:inline-block;margin:6px 8px 0 0;padding:10px 16px;background:#154273;color:#fff;border-radius:4px;text-decoration:none}}</style></head>
<body><h1>Inloggen als inwoner</h1>
<p>Je bent ingelogd als <strong>{wie}</strong>. Dat is een medewerkersaccount zonder BSN, en MijnOverheid laat de gegevens van een inwoner zien.
Kies een testinwoner (DigiD demo, één klik):</p>
<p><a class="b" href="{klik}?als=suzanne&terug={terug}">Suzanne Moulin</a><a class="b" href="{klik}?als=lukas&terug={terug}">Lukas Klamer</a><a class="b" href="{klik}?als=merel&terug={terug}">Merel Kooyman</a></p>
</body></html>"""


class H(BaseHTTPRequestHandler):
    server_version = "mijnoverheid-adapter"

    def log_message(self, fmt, *args):  # geen query-strings of BSN's in de log
        print(f"{self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}", flush=True)

    def session(self):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "mo_session":
                return unsign(v)
        return None

    def cookie(self, name):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return None

    def send(self, code, body=b"", ctype="application/json", headers=None):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def redirect(self, to, cookies=()):
        self.send_response(302)
        self.send_header("Location", to)
        for c in cookies:
            self.send_header("Set-Cookie", c)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    # ---------- routes ----------
    def do_GET(self):
        self.route()

    def do_HEAD(self):
        self.route()

    def do_POST(self):
        self.route()

    def do_OPTIONS(self):
        self.send(204, b"")

    def route(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/login":
            # ?als=suzanne: opnieuw inloggen (ook als er al een sessie is, bijvoorbeeld als 'demo') met die gebruiker voorgevuld
            args = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
            state = secrets.token_urlsafe(16)
            params = {"client_id": CLIENT, "response_type": "code", "scope": "openid",
                      "redirect_uri": f"{ORIGIN}/oidc/callback", "state": state}
            if args.get("als"):
                params.update({"prompt": "login", "login_hint": args["als"]})
            q = urllib.parse.urlencode(params)
            return self.redirect(f"{KC}/auth?{q}", [f"mo_state={state}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=600"])
        if path == "/wissel":
            # Eerst de Keycloak-sessie van de huidige gebruiker beëindigen, dan inloggen als de gekozen testinwoner
            als = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query)).get("als", "suzanne")
            q = {"client_id": CLIENT, "post_logout_redirect_uri": f"{ORIGIN}/login?als={urllib.parse.quote(als)}"}
            if self.cookie("mo_idt"):
                q["id_token_hint"] = self.cookie("mo_idt")
            return self.redirect(f"{KC}/logout?{urllib.parse.urlencode(q)}",
                                 ["mo_idt=; Path=/; Max-Age=0", "mo_session=; Path=/; Max-Age=0"])
        if path == "/oidc/callback":
            return self.callback()
        if path == "/logout":
            q = urllib.parse.urlencode({"client_id": CLIENT, "post_logout_redirect_uri": f"{ORIGIN}/"})
            return self.redirect(f"{KC}/logout?{q}", ["mo_session=; Path=/; Max-Age=0; Secure; HttpOnly"])
        if path == "/.well-known/federated-resources":
            return self.manifest()
        if path.startswith("/.netlify/functions/chat"):
            return self.chat()
        if path.startswith("/.netlify/functions/"):
            return self.send(503, {"error": "not_configured"})
        if path.startswith("/apis/"):
            return self.api(path)
        return self.static(path)

    def callback(self):
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.path).query))
        if not q.get("code") or q.get("state") != self.cookie("mo_state"):
            return self.send(400, "Ongeldige login, probeer opnieuw via /login", "text/plain; charset=utf-8")
        r = http.post(f"{KC}/token", timeout=20, data={"grant_type": "authorization_code", "code": q["code"],
                      "redirect_uri": f"{ORIGIN}/oidc/callback", "client_id": CLIENT, "client_secret": CLIENT_SECRET})
        if r.status_code != 200:
            return self.send(400, "Inloggen mislukt", "text/plain; charset=utf-8")
        idt = r.json()["id_token"]
        claims = jwt.decode(idt, jwks.get_signing_key_from_jwt(idt).key, algorithms=["RS256"], audience=CLIENT)
        if not claims.get("bsn"):
            # id_token bewaren zodat /wissel de Keycloak-sessie zonder bevestigingsscherm kan beëindigen
            return self.send(403, GEEN_BSN.format(wie=html.escape(claims.get("preferred_username", "dit account")),
                                                  klik=f"https://keycloak.{D}/demo-login",
                                                  terug=urllib.parse.quote(f"{ORIGIN}/login", safe="")),
                             "text/html; charset=utf-8",
                             {"Set-Cookie": f"mo_idt={idt}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=600"})
        naam = " ".join(x for x in [claims.get("given_name"), claims.get("family_name")] if x) or "inwoner"
        sess = sign({"bsn": claims["bsn"], "naam": naam, "exp": int(time.time()) + 8 * 3600})
        self.redirect("/", [f"mo_session={sess}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=28800",
                            "mo_state=; Path=/; Max-Age=0"])

    def manifest(self):
        services = ["agenda", "gesprekken", "openplan-plannen", "producten", "taken", "zaken"]
        echt = {"taken", "zaken"}
        self.send(200, {"gemeente": GEMEENTE, "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "resources": [{"service": s, "baseUrl": f"{ORIGIN}/apis/rest/{s}/next",
                                       "specUrl": f"/docs/bundled/apis_rest_{s}_next.yaml",
                                       "label": f"{s} ({'Open Zaak en Objecten, aangevuld met mock' if s in echt else 'mock VNG API Lab'})"}
                                      for s in services]})

    def mock(self, path, raw=None):
        url = MOCK + self.path
        hdrs = {k: v for k, v in self.headers.items() if k.lower() in ("content-type", "accept", "prefer", "authorization")}
        r = http.request(self.command, url, headers=hdrs, data=raw if raw is not None else self.body(), timeout=20)
        return r

    def api(self, path):
        sess = self.session()
        try:
            if path == "/apis/rest/zaken/next/zaken/zoek" and self.command == "POST":
                raw = self.body()
                mock = self.mock(path, raw)
                eigen = [zaak_samenvatting(z) for z in eigen_zaken(sess["bsn"])] if sess else []
                return self.send(200, eigen + (mock.json() if mock.ok else []))
            if path.startswith("/apis/rest/zaken/next/zaken/") and self.command == "GET" and sess:
                uuid = path.rsplit("/", 1)[-1]
                z = next((z for z in eigen_zaken(sess["bsn"]) if z["uuid"] == uuid), None)
                if z:
                    return self.send(200, zaak_detail(z, sess["bsn"]))
            if path == "/apis/rest/taken/next/context/zoek" and self.command == "POST":
                raw = self.body()
                mock = self.mock(path, raw)
                data = mock.json() if mock.ok else {}
                if sess:
                    data["taken"] = [taak_samenvatting(t) for t in eigen_taken(sess["bsn"])] + data.get("taken", [])
                return self.send(200, data)
            if path.startswith("/apis/rest/taken/next/taken/") and self.command == "GET" and sess:
                uuid = path.rsplit("/", 1)[-1]
                t = next((t for t in eigen_taken(sess["bsn"]) if t["_uuid"] == uuid), None)
                if t:
                    return self.send(200, taak_samenvatting(t))
            if path.startswith("/apis/rest/openklant-klantinteracties/") and "/partijen/" in path and sess:
                return self.send(200, gegevens_partij(sess["bsn"]))
            r = self.mock(path)
            return self.send(r.status_code, r.content, r.headers.get("Content-Type", "application/json"))
        except requests.RequestException as e:
            return self.send(502, {"error": "upstream", "detail": type(e).__name__})

    def chat(self):
        if self.command == "OPTIONS":
            return self.send(204, b"")
        if not OPENROUTER_KEY:
            return self.send(503, {"error": "not_configured"})
        try:
            body = json.loads(self.body() or b"{}")
        except ValueError:
            return self.send(400, {"error": "invalid_json"})
        body["model"] = OPENROUTER_MODEL
        r = http.post("https://openrouter.ai/api/v1/chat/completions", json=body, stream=True, timeout=120,
                      headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "HTTP-Referer": ORIGIN, "X-Title": "MijnOverheid demo"})
        self.send_response(r.status_code)
        self.send_header("Content-Type", r.headers.get("Content-Type", "text/event-stream"))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        for chunk in r.iter_content(chunk_size=None):
            self.wfile.write(chunk); self.wfile.flush()

    def static(self, path):
        f = os.path.normpath(os.path.join(STATIC, path.lstrip("/")))
        if not f.startswith(STATIC):
            return self.send(404, b"")
        if os.path.isfile(f) and not f.endswith("index.html"):
            ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
            with open(f, "rb") as fh:
                return self.send(200, fh.read(), ctype, {"Cache-Control": "public, max-age=3600"})
        sess = self.session()
        if not sess:
            return self.redirect("/login")
        with open(os.path.join(STATIC, "index.html"), encoding="utf-8") as fh:
            html = fh.read()
        inject = f"<script>window.__MO_NAAM__={json.dumps(sess['naam'])};</script>"
        return self.send(200, html.replace("</head>", inject + "</head>"), "text/html; charset=utf-8",
                         {"Cache-Control": "no-store"})


if __name__ == "__main__":
    print("mijnoverheid-adapter op :8080", flush=True)
    ThreadingHTTPServer(("", 8080), H).serve_forever()
