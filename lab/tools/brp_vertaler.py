"""BRP-vertaler: de GBA-variant-mock als "BRP API Personen 2" (officieel formaat).

De BRP-mock van de demogemeente (iswish/haal-centraal-brp-bevragen-gba-mock) geeft
antwoorden in de GBA-variant: datums als "JJJJMMDD" en een platte verblijfplaats.
Afnemers die de officiele BRP API Personen 2.x verwachten (Open Inwoner 2.4 valideert
het antwoord met pydantic) weigeren dat. Deze vertaler stuurt het verzoek door naar de
mock en zet het antwoord om:

- elke "datum..."-waarde van 8 cijfers wordt {"type": "Datum", "datum": "JJJJ-MM-DD",
  "langFormaat": "..."};
- verblijfplaats wordt {"type": "Adres", "verblijfadres": {...}, ...};
- leeftijd wordt uitgerekend als de geboortedatum bekend is.

Het officiele mock-image (ghcr.io/brp-api/personen-mock) zou dit overbodig maken, maar
ghcr.io was in de bouwomgeving niet bereikbaar. Alleen voor de demo.

POST /haalcentraal/api/brp/personen   vertaald antwoord
GET  /health                          200
"""
import json
import os
import urllib.error
import urllib.request
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BRON = os.environ.get("BRP_BRON", "http://brp-mock.local:80").rstrip("/")
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september",
           "oktober", "november", "december"]


def datum(waarde):
    if isinstance(waarde, str) and len(waarde) == 8 and waarde.isdigit():
        j, m, d = waarde[:4], waarde[4:6], waarde[6:]
        if m == "00" or d == "00":
            return {"type": "DatumOnvolledig", "jaar": int(j), "langFormaat": j}
        return {"type": "Datum", "datum": f"{j}-{m}-{d}", "langFormaat": f"{int(d)} {MAANDEN[int(m) - 1]} {j}"}
    return waarde


def vertaal(obj):
    if isinstance(obj, list):
        return [vertaal(x) for x in obj]
    if not isinstance(obj, dict):
        return obj
    uit = {}
    for k, v in obj.items():
        if k.startswith("datum") and isinstance(v, str):
            uit[k] = datum(v)
        else:
            uit[k] = vertaal(v)
    return uit


def verblijfplaats(vp):
    if not isinstance(vp, dict) or "verblijfadres" in vp:
        return vp
    adres_velden = ("huisnummer", "huisletter", "huisnummertoevoeging", "aanduidingBijHuisnummer", "postcode",
                    "woonplaats")
    adres = {k: vp[k] for k in adres_velden if k in vp}
    if "naamOpenbareRuimte" in vp:
        adres["officieleStraatnaam"] = vp["naamOpenbareRuimte"]
    if "straat" in vp:
        adres["korteStraatnaam"] = vp["straat"]
    uit = {k: v for k, v in vp.items() if k not in adres_velden + ("naamOpenbareRuimte", "straat")}
    uit["type"] = "Adres" if adres else "VerblijfplaatsOnbekend"
    if adres:
        uit["verblijfadres"] = adres
    return uit


def persoon(p):
    gba_geboorte = (p.get("geboorte") or {}).get("datum")
    p = vertaal(p)
    if "verblijfplaats" in p:
        p["verblijfplaats"] = verblijfplaats(p["verblijfplaats"])
    if isinstance(gba_geboorte, str) and len(gba_geboorte) == 8 and gba_geboorte[4:6] != "00":
        g = date(int(gba_geboorte[:4]), int(gba_geboorte[4:6]), int(gba_geboorte[6:8] or 1) or 1)
        vandaag = date.today()
        p.setdefault("leeftijd", vandaag.year - g.year - ((vandaag.month, vandaag.day) < (g.month, g.day)))
    return p


class Handler(BaseHTTPRequestHandler):
    def _antwoord(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self._antwoord(200, {"status": "ok"})
        return self._antwoord(405, {"fout": "alleen POST"})

    def do_POST(self):
        lengte = int(self.headers.get("Content-Length") or 0)
        verzoek = urllib.request.Request(BRON + self.path, data=self.rfile.read(lengte), method="POST",
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(verzoek, timeout=30) as r:
                status, ruw = r.status, r.read()
        except urllib.error.HTTPError as e:
            return self._antwoord(e.code, e.read(), e.headers.get("Content-Type", "application/json"))
        try:
            body = json.loads(ruw)
        except ValueError:
            return self._antwoord(status, ruw)
        if isinstance(body, dict) and isinstance(body.get("personen"), list):
            body["personen"] = [persoon(p) for p in body["personen"]]
        return self._antwoord(status, body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
