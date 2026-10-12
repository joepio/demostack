"""Koppeling tussen ZaakChat en de DemoStack.

- Inloggen: ZaakChat kent alleen een magic link per e-mail. Deze koppeling logt in via Keycloak (single sign-on)
  en geeft daarna een kortlevende ZaakChat-inlogtoken af voor het e-mailadres uit Keycloak.
- Zaken: Open Notificaties meldt nieuwe zaken en statuswijzigingen (kanaal 'zaken'). De koppeling zet elke zaak
  van een testinwoner om naar een ZaakChat-zaak (Issue), met de inwoner en de behandelaars als betrokkenen,
  en elke status als bericht in de tijdlijn. De planning toont de stappen van het zaaktype met datums.
  Bij het starten worden bestaande zaken ingelezen.
ZaakChat zelf blijft ongewijzigd.
"""
import json, os, secrets, threading, time, urllib.parse, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import jwt, requests

D = os.environ["BASE_DOMAIN"]
ORIGIN = f"https://zaakchat.{D}"
ZC = os.environ.get("ZAAKCHAT_URL", "http://zaakchat:8000")
ZC_SECRET = os.environ["ZAAKCHAT_JWT_SECRET"]
KC = f"https://keycloak.{D}/realms/demogemeente/protocol/openid-connect"
CLIENT, CLIENT_SECRET = "zaakchat", os.environ["ZAAKCHAT_OIDC_SECRET"]
OZ = f"https://zaken.{D}"
ZGW_ID, ZGW_SECRET = "zaakchat", os.environ["ZAAKCHAT_ZGW_SECRET"]
ON_AUTH = os.environ["ZAAKCHAT_ON_KEY"]
# BSN van testinwoners -> e-mailadres in Keycloak (ZaakChat herkent mensen aan hun e-mail)
INWONERS = dict(p.split("=", 1) for p in os.environ.get("ZAAKCHAT_INWONERS", "").split(",") if "=" in p)
MEDEWERKERS = [e for e in os.environ.get("ZAAKCHAT_MEDEWERKERS", "").split(",") if e]
GEMEENTE = os.environ.get("ZAAKCHAT_GEMEENTE", f"gemeente@{D}")
jwks = jwt.PyJWKClient(f"{KC}/certs")
http = requests.Session()


def zc_token(email, minutes=15):
    now = int(time.time())
    return jwt.encode({"sub": email, "iat": now, "exp": now + minutes * 60}, ZC_SECRET, algorithm="HS256")


def zgw():
    t = jwt.encode({"iss": ZGW_ID, "iat": int(time.time()), "client_id": ZGW_ID, "user_id": ZGW_ID,
                    "user_representation": "ZaakChat-koppeling"}, ZGW_SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326"}


def oz(url, **params):
    r = http.get(url, headers=zgw(), params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def commit(subject, schema, resource_id, data=None, patch=None):
    ev = {"specversion": "1.0", "id": str(uuid.uuid4()), "source": "demostack-open-zaak", "subject": subject,
          "type": "json.commit", "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
          "datacontenttype": "application/json", "dataschema": f"{ORIGIN}/schemas/JSONCommit",
          "data": {"schema": f"{ORIGIN}/schemas/{schema}", "resource_id": resource_id, "actor": GEMEENTE,
                   **({"resource_data": data} if data is not None else {}), **({"patch": patch} if patch is not None else {})}}
    r = http.post(f"{ZC}/events", json=ev, timeout=20,
                  headers={"Authorization": f"Bearer {zc_token(GEMEENTE)}"})
    r.raise_for_status()


def bestaat(resource_id):
    r = http.get(f"{ZC}/resources/{resource_id}", timeout=20, headers={"Authorization": f"Bearer {zc_token(GEMEENTE)}"})
    return r.status_code == 200


def inwoner_van(zaak):
    for rol in oz(f"{OZ}/zaken/api/v1/rollen", zaak=zaak["url"]).get("results", []):
        bsn = (rol.get("betrokkeneIdentificatie") or {}).get("inpBsn")
        if bsn and bsn in INWONERS:
            return INWONERS[bsn]
    return None


def sync_zaak(url):
    zaak = oz(url)
    email = inwoner_van(zaak)
    if not email:
        return  # alleen zaken van testinwoners; andere zaken hebben geen bekend e-mailadres
    zid = zaak["uuid"]
    zt = oz(zaak["zaaktype"])
    if not bestaat(zid):
        commit(zid, "Issue", zid, data={
            "title": f"{zt['omschrijving']}: {zaak.get('omschrijving') or zaak['identificatie']}",
            "description": (zaak.get("toelichting") or "") + f"\n\nZaaknummer {zaak['identificatie']} in Open Zaak.",
            "status": "open", "assignee": MEDEWERKERS[0] if MEDEWERKERS else None,
            "involved": [email] + MEDEWERKERS})
    statustypen = {s["url"]: s for s in oz(f"{OZ}/catalogi/api/v1/statustypen", zaaktype=zaak["zaaktype"])["results"]}
    statussen = sorted(oz(f"{OZ}/zaken/api/v1/statussen", zaak=zaak["url"])["results"], key=lambda s: s["datumStatusGezet"])
    planning(zaak, zt, statustypen, statussen)
    for i, st in enumerate(statussen):
        cid = f"status-{st['uuid']}"
        if bestaat(cid):
            continue
        tekst = statustypen.get(st["statustype"], {})
        regel = tekst.get("statustekst") or tekst.get("omschrijving") or "Status gewijzigd"
        commit(zid, "Comment", cid, data={"content": f"Status: {regel}" + (f"\n{st['statustoelichting']}" if st.get("statustoelichting") else "")})
        nieuw = "closed" if zaak.get("einddatum") and i == len(statussen) - 1 else ("in_progress" if i > 0 else "open")
        commit(zid, "Issue", zid, patch={"status": nieuw})


def dagen(duur):
    """ISO 8601-duur zoals P14D of P2W naar dagen (alleen dagen en weken, genoeg voor zaaktypen)."""
    import re
    m = re.fullmatch(r"P(?:(\d+)W)?(?:(\d+)D)?", duur or "")
    return (int(m.group(1) or 0) * 7 + int(m.group(2) or 0)) if m else None


def planning(zaak, zt, statustypen, statussen):
    """Planning links in ZaakChat: de stappen (statustypen) van het zaaktype, met datum en voortgang.
    Bereikte stappen krijgen de datum waarop ze bereikt zijn, de laatste stap de streefdatum van het zaaktype."""
    from datetime import date, timedelta
    stappen = sorted(statustypen.values(), key=lambda s: s["volgnummer"])
    bereikt = {}
    for st in statussen:  # oud naar nieuw; eerste keer bereikt telt
        bereikt.setdefault(st["statustype"], st["datumStatusGezet"][:10])
    huidig = statussen[-1]["statustype"] if statussen else None
    nr_huidig = statustypen.get(huidig, {}).get("volgnummer", 0)
    eind = zaak.get("uiterlijkeEinddatumAfdoening") or zaak.get("einddatumGepland")
    if not eind and dagen(zt.get("doorlooptijd")) is not None:
        eind = (date.fromisoformat(zaak["startdatum"]) + timedelta(days=dagen(zt["doorlooptijd"]))).isoformat()
    momenten = []
    for i, st in enumerate(stappen):
        if zaak.get("einddatum") or st["volgnummer"] < nr_huidig:
            status = "completed"
        elif st["url"] == huidig:
            status = "current"
        else:
            status = "planned"
        datum = bereikt.get(st["url"]) or (eind if i == len(stappen) - 1 else None)
        momenten.append({"title": st.get("statustekst") or st["omschrijving"], "status": status, **({"date": datum} if datum else {})})
    pid = f"planning-{zaak['uuid']}"
    data = {"title": f"Afhandeling {zt['omschrijving'].lower()}",
            "description": f"Volgens het zaaktype {zt['omschrijving']}" +
                           (f": afgehandeld binnen {dagen(zt['doorlooptijd'])} dagen." if dagen(zt.get("doorlooptijd")) else "."),
            "moments": momenten}
    if bestaat(pid):
        commit(zaak["uuid"], "Planning", pid, patch=data)
    else:
        commit(zaak["uuid"], "Planning", pid, data=data)


def eerste_import():
    for poging in range(30):
        try:
            for bsn in INWONERS:
                for z in oz(f"{OZ}/zaken/api/v1/zaken", rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=bsn)["results"]:
                    sync_zaak(z["url"])
            print("eerste import klaar", flush=True)
            return
        except requests.RequestException as e:
            print("eerste import mislukt, opnieuw:", type(e).__name__, flush=True)
            time.sleep(10)


class H(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"{self.command} {self.path.split('?')[0]} {args[1] if len(args) > 1 else ''}", flush=True)

    def cookie(self, name):
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == name:
                return v
        return None

    def send(self, code, body=b"", ctype="text/plain; charset=utf-8", headers=()):
        body = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in headers:
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        if u.path == "/koppeling/login":
            state = secrets.token_urlsafe(16)
            p = {"client_id": CLIENT, "response_type": "code", "scope": "openid email",
                 "redirect_uri": f"{ORIGIN}/koppeling/callback", "state": state}
            if q.get("als"):
                p.update({"prompt": "login", "login_hint": q["als"]})
            return self.send(302, headers=[("Location", f"{KC}/auth?{urllib.parse.urlencode(p)}"),
                                           ("Set-Cookie", f"zc_state={state}; Path=/koppeling; HttpOnly; Secure; SameSite=Lax; Max-Age=600")])
        if u.path == "/koppeling/callback":
            if not q.get("code") or q.get("state") != self.cookie("zc_state"):
                return self.send(400, "Ongeldige login, probeer opnieuw via /koppeling/login")
            r = http.post(f"{KC}/token", timeout=20, data={"grant_type": "authorization_code", "code": q["code"],
                          "redirect_uri": f"{ORIGIN}/koppeling/callback", "client_id": CLIENT, "client_secret": CLIENT_SECRET})
            if r.status_code != 200:
                return self.send(400, "Inloggen mislukt")
            idt = r.json()["id_token"]
            claims = jwt.decode(idt, jwks.get_signing_key_from_jwt(idt).key, algorithms=["RS256"], audience=CLIENT)
            if not claims.get("email"):
                return self.send(403, "Dit account heeft geen e-mailadres")
            return self.send(302, headers=[("Location", f"{ORIGIN}/verify-login?token={zc_token(claims['email'])}"),
                                           ("Set-Cookie", "zc_state=; Path=/koppeling; Max-Age=0")])
        if u.path == "/koppeling/health":
            return self.send(200, "ok")
        return self.send(404, "niet gevonden")

    def do_POST(self):
        if urllib.parse.urlsplit(self.path).path != "/koppeling/notificaties":
            return self.send(404, "niet gevonden")
        if self.headers.get("Authorization") != ON_AUTH:
            return self.send(403, "geen toegang")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            msg = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self.send(400, "ongeldige json")
        if msg.get("kanaal") == "zaken" and msg.get("hoofdObject"):
            threading.Thread(target=self.verwerk, args=(msg["hoofdObject"],), daemon=True).start()
        return self.send(204)

    @staticmethod
    def verwerk(url):
        try:
            sync_zaak(url)
        except Exception as e:  # een mislukte notificatie mag de koppeling niet stoppen
            print("notificatie mislukt:", type(e).__name__, str(e)[:200], flush=True)


if __name__ == "__main__":
    threading.Thread(target=eerste_import, daemon=True).start()
    print("zaakchat-koppeling op :8080", flush=True)
    ThreadingHTTPServer(("", 8080), H).serve_forever()
