"""Gedeelde helpers voor seed- en smoke-scripts: API-clients en authenticatie.

Draait in de "tools"-container (image van Open Zaak, die requests en PyJWT
bevat) binnen het docker-netwerk, zodat alle URL's interne hostnamen zijn.
"""
import base64
import os
import time

import jwt
import requests

# Interne adressen. Elke stack gebruikt voor hetzelfde component dezelfde hostnaam
# (netwerkalias), zodat seed en tests in alle stacks werken. Afwijken kan met
# URL_<NAAM> in de omgeving van de tools-container.
def _url(naam, standaard):
    return os.environ.get(f"URL_{naam}", standaard).rstrip("/")


OPENZAAK = _url("OPENZAAK", "http://openzaak.local:8000")
OPENNOTIFICATIES = _url("OPENNOTIFICATIES", "http://opennotificaties.local:8000")
OPENOBJECT = _url("OPENOBJECT", "http://openobject.local:8000")
# Objecttypen: in Open Object 4 dezelfde applicatie als de Objecten API; met losse API's
# (stack dimpact, zoals PodiumD) een eigen hostnaam via URL_OBJECTTYPEN.
OBJECTTYPEN = _url("OBJECTTYPEN", OPENOBJECT)
OPENKLANT = _url("OPENKLANT", "http://openklant.local:8000")
OPENPRODUCT = _url("OPENPRODUCT", "http://openproduct.local:8000")
BRP = _url("BRP", "http://brp-mock.local:80")
SELECTIELIJST = _url("SELECTIELIJST", "http://selectielijst.local:8000")
KEYCLOAK = _url("KEYCLOAK", "http://keycloak.local:8080")
SINK = _url("SINK", "http://notificatie-sink.local:8080")
REFERENTIELIJSTEN = _url("REFERENTIELIJSTEN", "http://referentielijsten.local:8000")


def stack_componenten():
    """Component-id's van de actieve stack (DEMO_STACK), uit stacks/*/stack.yaml.

    Geeft None als er geen stack bekend is; dan gaat de seed uit van alles uit stack kern.
    Componenten met `seed: false` in het manifest tellen niet mee.
    """
    import sys
    from pathlib import Path

    stack = os.environ.get("DEMO_STACK")
    root = Path(__file__).resolve().parent.parent
    if not stack or not (root / "stacks" / stack / "stack.yaml").exists():
        return None
    sys.path.insert(0, str(root / "tests"))
    from kader import laad_manifest  # noqa: PLC0415

    return {c["id"] for c in laad_manifest(stack)["componenten"] if c.get("seed", True)}


CRS = {"Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}


def env(naam):
    waarde = os.environ.get(naam)
    if not waarde:
        raise SystemExit(f"omgevingsvariabele {naam} ontbreekt (zie .env)")
    return waarde


class ApiFout(Exception):
    pass


class Client:
    """Kleine wrapper rond requests met nette foutmeldingen."""

    def __init__(self, basis, headers_fn, naam):
        self.basis = basis.rstrip("/")
        self.headers_fn = headers_fn
        self.naam = naam

    def url(self, pad):
        return pad if pad.startswith("http") else f"{self.basis}/{pad.lstrip('/')}"

    def verzoek(self, methode, pad, verwacht=(200, 201, 204), **kwargs):
        headers = {"Accept": "application/json", **self.headers_fn(), **kwargs.pop("headers", {})}
        # Geen gedeelde sessie: uWSGI sluit keep-alive-verbindingen soms, en dan
        # zou een hergebruikte verbinding een "connection reset" geven.
        pogingen = 4 if methode in ("GET", "HEAD") else 1
        for poging in range(pogingen):
            try:
                r = requests.request(methode, self.url(pad), headers=headers, timeout=60, **kwargs)
                break
            except requests.ConnectionError:
                if poging == pogingen - 1:
                    raise
                time.sleep(2)
        if r.status_code not in verwacht:
            raise ApiFout(f"{self.naam} {methode} {self.url(pad)} -> {r.status_code}: {r.text[:1500]}")
        if r.status_code == 204 or not r.content:
            return None
        try:
            return r.json()
        except ValueError:
            return r.text

    def get(self, pad, **kw):
        return self.verzoek("GET", pad, **kw)

    def post(self, pad, data, **kw):
        return self.verzoek("POST", pad, json=data, **kw)

    def patch(self, pad, data, **kw):
        return self.verzoek("PATCH", pad, json=data, **kw)

    def put(self, pad, data, **kw):
        return self.verzoek("PUT", pad, json=data, **kw)

    def delete(self, pad, **kw):
        return self.verzoek("DELETE", pad, **kw)

    def lijst(self, pad, **params):
        """Haalt alle resultaten op (volgt paginering)."""
        uit = []
        data = self.get(pad, params=params)
        while True:
            if isinstance(data, list):
                return uit + data
            uit.extend(data.get("results", []))
            volgende = data.get("next")
            if not volgende:
                return uit
            data = self.get(volgende)

    def eerste(self, pad, **params):
        data = self.get(pad, params=params)
        if isinstance(data, list):
            return data[0] if data else None
        resultaten = data.get("results", [])
        return resultaten[0] if resultaten else None


def zgw_token(client_id, secret):
    """ZGW-JWT (HS256) zoals Open Zaak en Open Notificaties die verwachten."""
    payload = {
        "iss": client_id,
        "iat": int(time.time()),
        "client_id": client_id,
        "user_id": client_id,
        "user_representation": client_id,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def zgw_client(basis, client_id, secret, naam):
    return Client(basis, lambda: {"Authorization": f"Bearer {zgw_token(client_id, secret)}", **CRS}, naam)


def token_client(basis, token, naam):
    return Client(basis, lambda: {"Authorization": f"Token {token}"}, naam)


def open_zaak_beheer():
    return zgw_client(OPENZAAK, env("ZGW_BEHEER_CLIENT_ID"), env("ZGW_BEHEER_SECRET"), "Open Zaak")


def open_zaak_portaal():
    return zgw_client(OPENZAAK, env("ZGW_PORTAAL_CLIENT_ID"), env("ZGW_PORTAAL_SECRET"), "Open Zaak (burgerportaal)")


def open_object(token_var="OPENOBJECT_BEHEER_TOKEN"):
    return token_client(f"{OPENOBJECT}/api/v2", env(token_var), "Open Object")


def objecttypen(token_var="OPENOBJECT_BEHEER_TOKEN"):
    """Objecttypen API: Open Object zelf, of de losse Objecttypen API (URL_OBJECTTYPEN)."""
    return token_client(f"{OBJECTTYPEN}/api/v2", env(token_var), "Objecttypen API")


def objecttype_url(uuid):
    return f"{OBJECTTYPEN}/api/v2/objecttypes/{uuid}"


def zorg_voor_objecttype(uuid, naam, schema, meervoud=None, omschrijving=""):
    """Zorgt voor een objecttype met een gepubliceerde versie (JSON-schema). Idempotent.

    In Open Object 4 bestaan de objecttypen al (setup-configuration); in een losse
    Objecttypen API maakt deze functie ze aan met de vaste UUID. Geeft True als er iets
    is aangemaakt of gepubliceerd.
    """
    ot = objecttypen()
    gewijzigd = False
    bestaand = ot.verzoek("GET", f"objecttypes/{uuid}", verwacht=(200, 404))
    if not (isinstance(bestaand, dict) and bestaand.get("uuid")):
        ot.post("objecttypes", {
            "uuid": uuid, "name": naam, "namePlural": meervoud or naam, "description": omschrijving,
            "dataClassification": "intern", "maintainerOrganization": env("GEMEENTE_NAAM"),
            "contactEmail": "beheer@voorbeeldstad.example", "updateFrequency": "unknown",
        })
        gewijzigd = True
    versies = ot.lijst(f"objecttypes/{uuid}/versions")
    if any(v.get("status") == "published" for v in versies):
        return gewijzigd
    if versies:
        versie = ot.patch(versies[0]["url"], {"jsonSchema": schema})
    else:
        versie = ot.post(f"objecttypes/{uuid}/versions", {"jsonSchema": schema, "status": "draft"})
    ot.patch(versie["url"], {"status": "published"})
    return True


def open_klant(token_var="OPENKLANT_BEHEER_TOKEN"):
    return token_client(f"{OPENKLANT}/klantinteracties/api/v1", env(token_var), "Open Klant")


def open_product(deel="producttypen"):
    return token_client(f"{OPENPRODUCT}/{deel}/api/v1", env("OPENPRODUCT_BEHEER_TOKEN"), f"Open Product ({deel})")


def brp():
    return Client(f"{BRP}/haalcentraal/api/brp", lambda: {"Content-Type": "application/json"}, "BRP-mock")


def brp_persoon(bsn):
    data = brp().post("personen", {
        "type": "RaadpleegMetBurgerservicenummer",
        "burgerservicenummer": [bsn],
        "fields": ["burgerservicenummer", "naam", "geboorte", "geslacht", "verblijfplaats"],
    })
    personen = data.get("personen", [])
    if not personen:
        raise ApiFout(f"BSN {bsn} niet gevonden in de BRP-mock")
    return personen[0]


def b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def maak_pdf(titel: str, regels: list[str]) -> bytes:
    """Maakt een minimale, geldige PDF met een titel en een paar regels tekst."""
    def esc(s):
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace").decode("latin-1")

    tekst = ["BT", "/F1 16 Tf", "50 790 Td", f"({esc(titel)}) Tj", "/F1 11 Tf"]
    for regel in regels:
        tekst += ["0 -20 Td", f"({esc(regel)}) Tj"]
    tekst.append("ET")
    stream = "\n".join(tekst).encode("latin-1")
    objecten = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    uit = bytearray(b"%PDF-1.4\n")
    posities = []
    for i, obj in enumerate(objecten, 1):
        posities.append(len(uit))
        uit += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(uit)
    uit += f"xref\n0 {len(objecten) + 1}\n0000000000 65535 f \n".encode()
    for p in posities:
        uit += f"{p:010d} 00000 n \n".encode()
    uit += f"trailer\n<< /Size {len(objecten) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(uit)
