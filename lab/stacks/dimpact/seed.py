"""Testdata voor stack "dimpact", na de gedeelde seed (seed/seed.py). Idempotent.

1. Wat stack maykin ook doet, voor de componenten die PodiumD deelt met het
   Maykin-landschap (stacks/maykin/seed.py): applicaties in Open Zaak voor Open
   Formulieren en Open Inwoner, objecttype "Externe taak" met taken (Mijn taken in Open
   Inwoner), vragen in Open Klant (Mijn vragen) en het formulier "Melding openbare
   ruimte" in Open Formulieren. Geen Open VTB: dat draait PodiumD niet.
2. PodiumD-objecttypen in de Objecttypen API (Afdeling, Groep, Medewerker,
   Activiteitenlog van ITA) en de afdelingen, groepen en medewerkers van Voorbeeldstad
   in de Objecten API. KISS en ITA kiezen daaruit bij een contactverzoek.
3. Actoren en contactverzoeken in Open Klant: een klantcontact met een interne taak,
   toegewezen aan een medewerker. Dat is wat KISS aanmaakt en ITA afhandelt.
4. Abonnement van NotifyNL OMC op kanaal "zaken" in Open Notificaties.

Gebruik (via scripts/stack.sh seed dimpact): python stacks/dimpact/seed.py
"""
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "seed"))

import jwt  # noqa: E402

from lib import (  # noqa: E402
    OPENNOTIFICATIES,
    ApiFout,
    env,
    objecttype_url,
    open_klant,
    open_object,
    open_zaak_beheer,
    zgw_client,
    zorg_voor_objecttype,
)

SCHEMAS = ROOT / "config" / "objecttypen" / "schemas"

# Vaste UUID's (ook in config/objecten/data.yaml en stacks/dimpact/compose.yml)
OT_AFDELING = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c1"
OT_GROEP = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c2"
OT_MEDEWERKER = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c3"
OT_LOGBOEK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000c4"

AFDELINGEN = [
    {"identificatie": "vergunningen", "naam": "Vergunningen", "email": "vergunningen@voorbeeldstad.example"},
    {"identificatie": "zorg-en-welzijn", "naam": "Zorg en Welzijn", "email": "wmo@voorbeeldstad.example"},
    {"identificatie": "kcc", "naam": "Klantcontactcentrum", "email": "kcc@voorbeeldstad.example"},
]
GROEPEN = [
    {"identificatie": "omgevingswet", "naam": "Team Omgevingswet", "afdeling": "vergunningen",
     "email": "omgevingswet@voorbeeldstad.example"},
    {"identificatie": "wmo-loket", "naam": "Wmo-loket", "afdeling": "zorg-en-welzijn",
     "email": "wmo-loket@voorbeeldstad.example"},
]
# Medewerkers: identificatie = gebruikersnaam in Keycloak-realm podiumd (claim
# preferred_username), zodat ITA de ingelogde medewerker aan zijn object koppelt.
MEDEWERKERS = [
    {"identificatie": "kcm.jansen", "voornaam": "Karin", "achternaam": "Jansen", "functie": "Klantcontactmedewerker",
     "afdeling": "Klantcontactcentrum", "groep": None, "email": "kcm.jansen@voorbeeldstad.example"},
    {"identificatie": "behandelaar.desai", "voornaam": "Ravi", "achternaam": "Desai", "functie": "Vergunningverlener",
     "afdeling": "Vergunningen", "groep": "Team Omgevingswet", "email": "behandelaar.desai@voorbeeldstad.example"},
    {"identificatie": "beheer.devries", "voornaam": "Mila", "achternaam": "de Vries", "functie": "Functioneel beheerder",
     "afdeling": "Klantcontactcentrum", "groep": None, "email": "beheer.devries@voorbeeldstad.example"},
]
# Contactverzoeken: (nummer, bsn, zaak, onderwerp, inhoud, medewerker, afdeling of groep).
# ITA toont een taak alleen aan leden van de afdeling of groep waaraan hij ook is
# toegewezen (ContactverzoekAutorisatieGuardService); een taak met alleen een
# medewerker-actor geeft 403, ook voor die medewerker zelf.
CONTACTVERZOEKEN = [
    ("8000000001", "999990627", "VBS-2026-000101", "Terugbelverzoek over de dakkapel",
     "Meneer Janssen vraagt of de aanvullende tekening ook per post mag. Graag terugbellen.", "behandelaar.desai",
     ("grp", "omgevingswet")),
    ("8000000002", "999997609", "VBS-2026-000104", "Vraag over de planning van de traplift",
     "Mevrouw De Crooy wil weten wanneer het keukentafelgesprek plaatsvindt.", "kcm.jansen",
     ("afd", "kcc")),
]

oz = open_zaak_beheer()


def log(msg):
    print(msg, flush=True)


def maykin_seed():
    """Laadt stacks/maykin/seed.py als module (zonder main uit te voeren)."""
    spec = importlib.util.spec_from_file_location("seed_maykin", ROOT / "stacks" / "maykin" / "seed.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------- PodiumD-objecttypen
def podiumd_objecttypen():
    for uuid, naam, meervoud, bestand in [
        (OT_AFDELING, "Afdeling", "Afdelingen", "afdeling.json"),
        (OT_GROEP, "Groep", "Groepen", "groep.json"),
        (OT_MEDEWERKER, "Medewerker", "Medewerkers", "medewerker.json"),
        (OT_LOGBOEK, "Activiteitenlog", "Activiteitenlogs", "logboek.json"),
    ]:
        schema = json.loads((SCHEMAS / bestand).read_text())
        if zorg_voor_objecttype(uuid, naam, schema, meervoud, f"PodiumD-objecttype {naam} (community-concept)"):
            log(f"objecttype gepubliceerd: {naam}")


def zorg_voor_object(oo, ot_uuid, data):
    type_url = objecttype_url(ot_uuid)
    bestaand = oo.eerste("objects", type=type_url, data_attr=f"identificatie__exact__{data['identificatie']}")
    if bestaand:
        return bestaand
    obj = oo.post("objects", {"type": type_url, "record": {"typeVersion": 1, "startAt": "2026-01-01", "data": data}},
                  headers={"Content-Crs": "EPSG:4326"})
    log(f"object aangemaakt: {data['identificatie']}")
    return obj


def organisatie():
    oo = open_object()
    afdelingen = {}
    for a in AFDELINGEN:
        afdelingen[a["identificatie"]] = zorg_voor_object(oo, OT_AFDELING, dict(a))
    for g in GROEPEN:
        data = {k: v for k, v in g.items() if k != "afdeling"}
        data["afdelingId"] = afdelingen[g["afdeling"]]["uuid"]
        zorg_voor_object(oo, OT_GROEP, data)
    for m in MEDEWERKERS:
        data = {
            "identificatie": m["identificatie"], "voornaam": m["voornaam"], "achternaam": m["achternaam"],
            "volledigeNaam": f"{m['voornaam']} {m['achternaam']}", "functie": m["functie"],
            "emails": [{"email": m["email"], "naam": f"{m['voornaam']} {m['achternaam']}"}],
            "telefoonnummers": [{"telefoonnummer": "14 0123"}],
            "afdelingen": [{"afdelingnaam": m["afdeling"]}],
            "groepen": [{"groepsnaam": m["groep"]}] if m["groep"] else [],
        }
        zorg_voor_object(oo, OT_MEDEWERKER, data)


# ------------------------------------------------ Open Klant: contactverzoeken
def zorg_voor_actor(ok, medewerker):
    m = next(x for x in MEDEWERKERS if x["identificatie"] == medewerker)
    bestaande = ok.lijst("actoren", actoridentificatorObjectId=medewerker)
    for a in bestaande:
        if (a.get("actoridentificator") or {}).get("codeRegister") == "obj":
            return a
    actor = ok.post("actoren", {
        "naam": f"{m['voornaam']} {m['achternaam']}", "soortActor": "medewerker", "indicatieActief": True,
        "actoridentificator": {"objectId": medewerker, "codeObjecttype": "mdw", "codeRegister": "obj",
                               "codeSoortObjectId": "idf"},
        "actorIdentificatie": {"functie": m["functie"], "emailadres": m["email"], "telefoonnummer": "0701234567"},
    })
    log(f"actor aangemaakt (Open Klant): {medewerker}")
    return actor


def zorg_voor_eenheid_actor(ok, soort, identificatie):
    """Actor voor een afdeling (afd) of groep (grp), zoals KISS die aanmaakt."""
    e = next(x for x in (AFDELINGEN if soort == "afd" else GROEPEN) if x["identificatie"] == identificatie)
    for a in ok.lijst("actoren", actoridentificatorObjectId=identificatie):
        if (a.get("actoridentificator") or {}).get("codeObjecttype") == soort:
            return a
    actor = ok.post("actoren", {
        "naam": e["naam"], "soortActor": "organisatorische_eenheid", "indicatieActief": True,
        "actoridentificator": {"objectId": identificatie, "codeObjecttype": soort, "codeRegister": "obj",
                               "codeSoortObjectId": "idf"},
        "actorIdentificatie": {"omschrijving": e["naam"], "emailadres": e["email"], "telefoonnummer": "0701234567"},
    })
    log(f"actor aangemaakt (Open Klant): {e['naam']}")
    return actor


def contactverzoeken(zaken):
    ok = open_klant()
    for nummer, bsn, zaaknummer, onderwerp, inhoud, medewerker, (soort, eenheid) in CONTACTVERZOEKEN:
        actoren = [{"uuid": zorg_voor_actor(ok, medewerker)["uuid"]},
                   {"uuid": zorg_voor_eenheid_actor(ok, soort, eenheid)["uuid"]}]
        bestaand = ok.eerste("klantcontacten", nummer=nummer)
        taak = bestaand and ok.eerste("internetaken", aanleidinggevendKlantcontact__uuid=bestaand["uuid"])
        if taak:
            huidig = {a["uuid"] for a in taak.get("toegewezenAanActoren") or []}
            if huidig != {a["uuid"] for a in actoren}:
                ok.patch(taak["url"], {"toegewezenAanActoren": actoren})
                log(f"interne taak {nummer} bijgewerkt: toegewezen aan {medewerker} en {eenheid}")
            continue
        partij = ok.eerste("partijen", partijIdentificator__objectId=bsn)
        if not partij:
            raise ApiFout(f"geen partij voor {bsn} in Open Klant (gedeelde seed gedraaid?)")
        kc = bestaand or ok.post("klantcontacten", {
            "nummer": nummer, "kanaal": "telefoon", "onderwerp": onderwerp, "inhoud": inhoud,
            "indicatieContactGelukt": True, "taal": "nld", "vertrouwelijk": False,
            "plaatsgevondenOp": "2026-10-05T10:15:00+02:00",
        })
        if not bestaand:
            naam = partij["partijIdentificatie"]["contactnaam"]
            ok.post("betrokkenen", {
                "wasPartij": {"uuid": partij["uuid"]}, "hadKlantcontact": {"uuid": kc["uuid"]},
                "rol": "klant", "initiator": True, "organisatienaam": "",
                "contactnaam": {k: naam.get(k, "") for k in ("voorletters", "voornaam", "voorvoegselAchternaam",
                                                              "achternaam")},
            })
            zaak = zaken.get(zaaknummer)
            if zaak:
                ok.post("onderwerpobjecten", {
                    "klantcontact": {"uuid": kc["uuid"]}, "wasKlantcontact": None,
                    "onderwerpobjectidentificator": {"objectId": zaak["uuid"], "codeObjecttype": "zgw-Zaak",
                                                     "codeRegister": "openzaak", "codeSoortObjectId": "uuid"},
                })
        ok.post("internetaken", {
            "nummer": nummer, "gevraagdeHandeling": "Contact opnemen met betrokkene",
            "aanleidinggevendKlantcontact": {"uuid": kc["uuid"]},
            "toegewezenAanActoren": actoren,
            "toelichting": inhoud, "status": "te_verwerken",
        })
        log(f"contactverzoek aangemaakt (Open Klant): {onderwerp} -> {medewerker} ({eenheid})")


# ------------------------------------------- Open Notificaties: OMC-abonnement
def omc_abonnement():
    nrc = zgw_client(OPENNOTIFICATIES, env("ZGW_BEHEER_CLIENT_ID"), env("ZGW_BEHEER_SECRET"), "Open Notificaties")
    callback = "http://omc.local:8080/Events/Listen"
    bestaand = [a for a in nrc.lijst("api/v1/abonnement") if a["callbackUrl"] == callback]
    # OMC controleert een eigen JWT (OMC_AUTH_JWT_*); geldig tot ver na de demo
    token = jwt.encode({"iss": "open-notificaties", "aud": "omc", "client_id": "open-notificaties",
                        "user_id": "open-notificaties", "user_representation": "Open Notificaties",
                        "iat": int(time.time()), "exp": int(time.time()) + 10 * 365 * 24 * 3600},
                       env("OMC_AUTH_JWT_SECRET"), algorithm="HS256")
    body = {"callbackUrl": callback, "auth": f"Bearer {token}",
            "kanalen": [{"naam": "zaken", "filters": {}}, {"naam": "objecten", "filters": {}}]}
    if bestaand:
        nrc.put(bestaand[0]["url"], body)
        log("abonnement OMC bijgewerkt")
    else:
        nrc.post("api/v1/abonnement", body)
        log("abonnement OMC aangemaakt (kanalen zaken en objecten)")


def main():
    log("== Seed stack dimpact")
    m = maykin_seed()
    m.applicaties()
    m.objecttype_externe_taak()
    zaken = {z["identificatie"]: z for z in oz.lijst("zaken/api/v1/zaken", bronorganisatie=env("GEMEENTE_RSIN"))}
    m.externe_taken(zaken)
    m.vragen()
    m.formulier()
    podiumd_objecttypen()
    organisatie()
    contactverzoeken(zaken)
    omc_abonnement()
    log("== Seed stack dimpact klaar")


if __name__ == "__main__":
    os.environ.setdefault("PORT_OPENFORMULIEREN", "8102")
    try:
        main()
    except ApiFout as e:
        print(f"FOUT: {e}", file=sys.stderr)
        sys.exit(1)
