"""Testdata en inrichting voor stack "g4", na de gedeelde seed (seed/seed.py). Idempotent.

1. Applicaties in Open Zaak voor Open Formulieren (meldingen registreren) en NL Portal
   (lezen), met autorisaties per zaaktype. GZAC heeft alle autorisaties (setup-config).
2. Objecttypen in Open Object met hun JSON-schema: "Taak" (taak v2, NL Portal),
   "Bericht" (NL Portal) en "Portaaltaak" (taak v1, de Portaaltaak-plugin van GZAC).
3. Taken (v2) en berichten voor burgers A en B in Open Object, zoals een G4-gemeente ze
   voor NL Portal klaarzet.
4. Taken in Open VTB (takenbron voor portalen) en vragen in Open Klant, zoals in maykin.
5. Formulier "Melding openbare ruimte" in Open Formulieren (uit stacks/maykin/seed.py).
6. GZAC: een aanvraag parkeervergunning van burger A. GZAC maakt daarvoor de zaak in
   Open Zaak (met initiator en statussen) en een portaaltaak in Open Object. De
   inrichting zelf (case, proces, plugins, zaaktypekoppeling) deployt GZAC bij het
   starten uit config/gzac/.

Gebruik (via scripts/stack.sh seed g4): python stacks/g4/seed.py
"""
import importlib.util
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "seed"))

from lib import ApiFout, env, objecttype_url, open_object, zorg_voor_objecttype  # noqa: E402

# Hergebruik uit stack maykin: Open VTB-taken, vragen in Open Klant, het formulier
_spec = importlib.util.spec_from_file_location("maykin_seed", ROOT / "stacks" / "maykin" / "seed.py")
maykin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(maykin)

oz = maykin.oz
KEYCLOAK = "http://keycloak.local:8080"
GZAC = os.environ.get("URL_GZAC", "http://gzac-backend.local:8000")
PUBLIEK_NLPORTAL = f"http://localhost:{os.environ.get('PORT_NLPORTAL', '8203')}"

OBJECTTYPE_TAAK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c1"
OBJECTTYPE_BERICHT = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c2"
OBJECTTYPE_PORTAALTAAK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c3"
CASE = "parkeervergunning"
CASE_VERSIE = "1.0.0"
PROCES = "behandelen-parkeervergunning"
BURGER_A = "999990627"
# De GZAC-aanvraag hoort bij een eigen testburger (D, Jeroen Altena), zodat de vaste
# verwachtingen van de gedeelde testsuite voor A, B en C (precies hun seedzaken) blijven kloppen.
BURGER_GZAC = "999991991"
NAAM_GZAC = "Jeroen Altena"
BURGER_B = "999997609"


def log(msg):
    print(msg, flush=True)


# ------------------------------------------------------------- Open Zaak
def applicaties():
    zaaktypen, iots = maykin.zaaktype_urls()
    mor = zaaktypen["VBS-MOR"]
    of_aut = [
        {"component": "ztc", "scopes": ["catalogi.lezen"]},
        {"component": "zrc", "scopes": ["zaken.lezen", "zaken.aanmaken", "zaken.bijwerken"],
         "zaaktype": mor["url"], "maxVertrouwelijkheidaanduiding": "zaakvertrouwelijk"},
    ]
    for omschrijving in ("Melding", "Foto"):
        of_aut.append({"component": "drc", "scopes": ["documenten.lezen", "documenten.aanmaken"],
                       "informatieobjecttype": iots[omschrijving]["url"],
                       "maxVertrouwelijkheidaanduiding": "zaakvertrouwelijk"})
    maykin.zorg_voor_applicatie("open-formulieren", "Open Formulieren (meldingen registreren)", of_aut)

    # NL Portal: lezen, zoals Open Inwoner in stack maykin. Zaken tot en met vertrouwelijk,
    # documenten tot en met zaakvertrouwelijk.
    nlp_aut = [{"component": "ztc", "scopes": ["catalogi.lezen"]}]
    for zt in zaaktypen.values():
        nlp_aut.append({"component": "zrc", "scopes": ["zaken.lezen"], "zaaktype": zt["url"],
                        "maxVertrouwelijkheidaanduiding": "vertrouwelijk"})
    for iot in iots.values():
        nlp_aut.append({"component": "drc", "scopes": ["documenten.lezen"], "informatieobjecttype": iot["url"],
                        "maxVertrouwelijkheidaanduiding": "zaakvertrouwelijk"})
    maykin.zorg_voor_applicatie("nl-portal", "NL Portal (burgerportaal, alleen lezen)", nlp_aut)

    # IKO (klantbeeld voor medewerkers): zaken lezen tot en met vertrouwelijk
    iko_aut = [{"component": "ztc", "scopes": ["catalogi.lezen"]}]
    for zt in zaaktypen.values():
        iko_aut.append({"component": "zrc", "scopes": ["zaken.lezen"], "zaaktype": zt["url"],
                        "maxVertrouwelijkheidaanduiding": "vertrouwelijk"})
    maykin.zorg_voor_applicatie("iko", "IKO (klantbeeld medewerkers, alleen lezen)", iko_aut)


# ------------------------------------------------------------ Open Object
def _datum_tijd(dag):
    return f"{dag}T23:59:00"


SCHEMA_TAAK_V2 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Taak (v2, NL Portal)",
    "type": "object",
    "required": ["titel", "status", "soort", "identificatie", "koppeling", "eigenaar"],
    "properties": {
        "titel": {"type": "string"},
        "status": {"type": "string", "enum": ["open", "afgerond", "verwerkt", "gesloten"]},
        "soort": {"type": "string", "enum": ["url", "portaalformulier", "ogonebetaling"]},
        "eigenaar": {"type": "string"},
        "verloopdatum": {"type": ["string", "null"]},
        "verwerker_taak_id": {"type": "string"},
        "identificatie": {"type": "object", "required": ["type", "value"],
                          "properties": {"type": {"type": "string"}, "value": {"type": "string"}}},
        "koppeling": {"type": "object", "properties": {"registratie": {"type": "string"},
                                                        "uuid": {"type": ["string", "null"]}}},
        "url": {"type": ["object", "null"]},
        "portaalformulier": {"type": ["object", "null"]},
        "ogonebetaling": {"type": ["object", "null"]},
    },
}

SCHEMA_BERICHT = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Bericht (NL Portal)",
    "type": "object",
    "required": ["onderwerp", "berichtTekst", "publicatiedatum", "identificatie"],
    "properties": {
        "onderwerp": {"type": "string"},
        "berichtTekst": {"type": "string"},
        "publicatiedatum": {"type": "string"},
        "referentie": {"type": "string"},
        "berichtType": {"type": "string"},
        "handelingsperspectief": {"type": "string"},
        "einddatumHandelingstermijn": {"type": ["string", "null"]},
        "geopend": {"type": "boolean"},
        "bijlages": {"type": "array"},
        "identificatie": {"type": "object", "required": ["type", "value"],
                          "properties": {"type": {"type": "string"}, "value": {"type": "string"}}},
    },
}

# Taak v1, zoals de Portaaltaak-plugin van GZAC 13 hem schrijft (TaakObject)
SCHEMA_PORTAALTAAK_V1 = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Portaaltaak (v1, GZAC)",
    "type": "object",
    "required": ["title", "status", "identificatie", "verwerker_taak_id"],
    "properties": {
        "title": {"type": "string"},
        "status": {"type": "string"},
        "identificatie": {"type": "object"},
        "data": {"type": ["object", "null"]},
        "formulier": {"type": ["object", "null"]},
        "zaak": {"type": ["string", "null"]},
        "verwerker_taak_id": {"type": "string"},
        "verloopdatum": {"type": ["string", "null"]},
        "verzonden_data": {"type": ["object", "null"]},
    },
}


def objecttypen():
    for uuid, naam, schema, meervoud in (
        (OBJECTTYPE_TAAK, "Taak", SCHEMA_TAAK_V2, "Taken"),
        (OBJECTTYPE_BERICHT, "Bericht", SCHEMA_BERICHT, "Berichten"),
        (OBJECTTYPE_PORTAALTAAK, "Portaaltaak", SCHEMA_PORTAALTAAK_V1, "Portaaltaken"),
    ):
        if zorg_voor_objecttype(uuid, naam, schema, meervoud):
            log(f"objecttype-versie gepubliceerd: {naam}")


# Taken voor NL Portal: (bsn, zaaknummer, titel, einddatum, soort)
TAKEN_V2 = [
    (BURGER_A, "VBS-2026-000101", "Aanvullende tekening dakkapel aanleveren", "2026-10-28", "url"),
    (BURGER_A, "VBS-2026-000102", "Vragenlijst over de afhandeling van uw melding", "2026-10-30", "url"),
    (BURGER_B, "VBS-2026-000104", "Medische verklaring traplift aanleveren", "2026-11-04", "url"),
]

BERICHTEN = [
    (BURGER_A, "Uw aanvraag dakkapel is in behandeling",
     "Wij hebben uw aanvraag voor een dakkapel ontvangen en beoordelen die nu. U hoort binnen acht weken van ons.",
     "VBS-2026-000101"),
    (BURGER_B, "Afspraak keukentafelgesprek traplift",
     "Een consulent van het Wmo-loket belt u deze week om een afspraak te maken.",
     "VBS-2026-000104"),
]


def taken_en_berichten(zaken):
    oo = open_object()
    type_taak = objecttype_url(OBJECTTYPE_TAAK)
    bestaand = {o["record"]["data"].get("verwerker_taak_id") for o in oo.lijst("objects", type=type_taak)}
    for nr, (bsn, zaaknummer, titel, einddatum, _soort) in enumerate(TAKEN_V2, 1):
        taak_id = f"00000000-0000-4000-8000-00000000c1{nr:02d}"
        if taak_id in bestaand:
            continue
        oo.post("objects", {"type": type_taak, "record": {"typeVersion": 1, "startAt": "2026-10-01", "data": {
            "titel": titel, "status": "open", "soort": "url", "eigenaar": "gemeente",
            "verwerker_taak_id": taak_id, "verloopdatum": _datum_tijd(einddatum),
            "identificatie": {"type": "bsn", "value": bsn},
            "koppeling": {"registratie": "zaak", "uuid": zaken[zaaknummer]["uuid"]},
            "url": {"uri": f"{maykin.PUBLIEK_OPENFORMULIEREN}/{maykin.FORMULIER_SLUG}"},
        }}}, headers={"Content-Crs": "EPSG:4326"})
        log(f"taak aangemaakt (Open Object, v2): {titel}")

    type_bericht = objecttype_url(OBJECTTYPE_BERICHT)
    bestaand = {o["record"]["data"].get("onderwerp"): o for o in oo.lijst("objects", type=type_bericht)}
    for bsn, onderwerp, tekst, zaaknummer in BERICHTEN:
        # NL Portal leest publicatiedatum en einddatumHandelingstermijn als LocalDateTime
        data = {
            "onderwerp": onderwerp, "berichtTekst": tekst, "publicatiedatum": "2026-10-02T09:00:00",
            "einddatumHandelingstermijn": "2026-11-02T23:59:00",
            "referentie": zaaknummer, "berichtType": "notificatie", "handelingsperspectief": "informatie verstrekken",
            "geopend": False, "bijlages": [], "identificatie": {"type": "bsn", "value": bsn},
        }
        record = {"typeVersion": 1, "startAt": "2026-10-01", "data": data}
        if onderwerp in bestaand:
            obj = bestaand[onderwerp]
            if {k: obj["record"]["data"].get(k) for k in data if k != "geopend"} != {k: v for k, v in data.items() if k != "geopend"}:
                oo.patch(f"objects/{obj['uuid']}", {"record": record}, headers={"Content-Crs": "EPSG:4326"})
                log(f"bericht bijgewerkt (Open Object): {onderwerp}")
            continue
        oo.post("objects", {"type": type_bericht, "record": record}, headers={"Content-Crs": "EPSG:4326"})
        log(f"bericht aangemaakt (Open Object): {onderwerp}")


# ------------------------------------------------------------------ GZAC
def gzac_token():
    r = requests.post(f"{KEYCLOAK}/realms/g4/protocol/openid-connect/token", timeout=30, data={
        "grant_type": "password", "client_id": "valtimo-console", "username": "beheer.yilmaz",
        "password": env("MEDEWERKER_WACHTWOORD"), "scope": "openid"})
    if r.status_code != 200:
        raise ApiFout(f"token voor GZAC (beheer.yilmaz) mislukt: {r.status_code} {r.text[:200]}")
    return r.json()["access_token"]


class Gzac:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {gzac_token()}"

    def req(self, methode, pad, ok=(200, 201, 204), **kw):
        r = self.s.request(methode, f"{GZAC}{pad}", timeout=60, **kw)
        if r.status_code not in ok:
            raise ApiFout(f"GZAC {methode} {pad}: {r.status_code} {r.text[:400]}")
        return r.json() if r.content and "json" in r.headers.get("Content-Type", "") else None


def wacht_op_gzac():
    for _ in range(60):
        try:
            r = requests.get(f"{GZAC}/api/v1/ping", timeout=5)
            if r.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise ApiFout("GZAC antwoordt niet")


def gzac_aanvraag(g):
    """Een aanvraag parkeervergunning van burger D, gestart in GZAC (zoals een
    medewerker of een formulierkoppeling dat doet)."""
    zaken = oz.lijst("zaken/api/v1/zaken", rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn=BURGER_GZAC)
    # GZAC laat Open Zaak het zaaknummer kiezen (ZAAK-...); de seedzaken heten VBS-...
    if any(not z["identificatie"].startswith("VBS-") for z in zaken):
        return
    g.req("POST", "/api/v1/process-document/operation/new-document-and-start-process", json={
        "processDefinitionKey": PROCES,
        "request": {"definition": CASE, "caseDefinitionKey": CASE, "caseDefinitionVersionTag": CASE_VERSIE,
                    "content": {"aanvrager": {"bsn": BURGER_GZAC, "naam": NAAM_GZAC},
                                "kenteken": "XX-999-X", "zone": "Centrum",
                                "toelichting": "Tweede auto in het huishouden"}}})
    log(f"GZAC: aanvraag parkeervergunning van burger D ({BURGER_GZAC}) gestart")


def main():
    log("== Seed stack g4")
    applicaties()
    objecttypen()
    zaken = {z["identificatie"]: z for z in oz.lijst("zaken/api/v1/zaken", bronorganisatie=env("GEMEENTE_RSIN"))}
    taken_en_berichten(zaken)
    maykin.vtb_taken()
    maykin.vragen()
    maykin.formulier()
    wacht_op_gzac()
    gzac_aanvraag(Gzac())
    log("== Seed stack g4 klaar")


if __name__ == "__main__":
    try:
        main()
    except ApiFout as e:
        print(f"FOUT: {e}", file=sys.stderr)
        sys.exit(1)
