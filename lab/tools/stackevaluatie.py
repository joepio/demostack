#!/usr/bin/env python3
"""Bouwt docs/stacks.json: per stack een evaluatie voor de stackpagina op de website.

Bronnen (alles uit deze repo, niets wordt live gemeten):
- stacks/<stack>/stack.yaml en stacks/basis/stack.yaml: welke componenten, welke rol
- results/<stack>.json: testresultaten, bekende fouten en de draaiende images (versies)
- docs/landschap/landschap.json: licentie, maker, API-standaarden en repo per component
- FOOTPRINT hieronder: gemeten geheugen, images en starttijd (docs/STACKS.md, 7 en 8 okt 2026)

Gebruik: python3 tools/stackevaluatie.py  (schrijft docs/stacks.json)
"""
import json
import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
STACKS = ["kern", "maykin", "dimpact", "g4", "vcg"]

# Gemeten op 15 GB geheugen en 4 CPU's, vanaf lege volumes (docs/STACKS.md, "Footprint").
FOOTPRINT = {
    "kern": {"geheugen_gib": 4.2, "images_gb": 8.3, "containers": 18, "start_s": 190,
             "zelf_gebouwd": []},
    "maykin": {"geheugen_gib": 7.5, "images_gb": 13.9, "containers": 27, "start_s": 327,
               "zelf_gebouwd": []},
    "dimpact": {"geheugen_gib": 9.0, "images_gb": 17.9, "containers": 36, "start_s": 346,
                "zelf_gebouwd": ["KISS", "ITA", "PABC"]},
    "g4": {"geheugen_gib": 8.0, "images_gb": 12.4, "containers": 30, "start_s": 330,
           "zelf_gebouwd": ["IKO", "NL Portal"]},
    "vcg": {"geheugen_gib": 7.1, "images_gb": 17.4, "containers": 39, "start_s": 309,
            "zelf_gebouwd": ["OpenRegister", "WordPress (OpenPDC, OpenPub)", "OpenPlan"]},
}

OMSCHRIJVING = {
    "kern": "Alleen de registers en hun API's: de basis waar elke andere stack op bouwt.",
    "maykin": "De producten van Maykin Media: Open Formulieren, Open Inwoner en Open VTB op de registers.",
    "dimpact": "Wat PodiumD 4.9.3 draait, het platform van Dimpact voor ongeveer 100 gemeenten.",
    "g4": "De keuze van de G4 (Platform Dienstverlening): NL Portal, GZAC/Valtimo en IKO op de registers.",
    "vcg": "De VCG-basisset: de vaste set componenten van de Voorziening Common Ground.",
}

# Functies voor de vergelijking per functie: welke componenten (id's uit stack.yaml) die
# functie invullen, en welke standaard-API's erbij horen.
FUNCTIES = [
    {"id": "melden", "naam": "Inwoner doet een aanvraag of melding",
     "componenten": ["openformulieren"],
     "apis": ["ZGW Zaken", "ZGW Documenten", "Objecten", "Haal Centraal BRP"]},
    {"id": "volgen", "naam": "Inwoner volgt zijn zaken en taken",
     "componenten": ["openinwoner", "nlportal"],
     "apis": ["ZGW Zaken", "Klantinteracties", "Objecten (taken)", "Mijn-API's (VNG API Lab)"]},
    {"id": "informeren", "naam": "Openbare informatie: producten, publicaties",
     "componenten": ["openpdc", "openpub", "publicatiebank", "openproduct"],
     "apis": ["Woo-publicaties", "Producten en diensten"]},
    {"id": "klantcontact", "naam": "KCC handelt een klantcontact af",
     "componenten": ["kiss"],
     "apis": ["Klantinteracties", "ZGW Zaken", "Haal Centraal BRP", "Objecten"]},
    {"id": "interne-taken", "naam": "Contactverzoek doorzetten naar een medewerker",
     "componenten": ["ita"],
     "apis": ["Klantinteracties", "Objecten"]},
    {"id": "zaak-afhandelen", "naam": "Behandelaar handelt een zaak af",
     "componenten": ["zac", "gzac", "operaton"],
     "apis": ["ZGW Zaken", "ZGW Catalogi", "ZGW Documenten", "ZGW Besluiten", "Notificaties"]},
    {"id": "klantbeeld", "naam": "Integraal beeld van een klant of object",
     "componenten": ["iko"],
     "apis": ["ZGW Zaken", "Klantinteracties", "Haal Centraal BRP"]},
    {"id": "registreren", "naam": "Registers: zaken, klanten, objecten",
     "componenten": ["openzaak", "openklant", "openobject", "objecttypen", "openvtb",
                     "openregister", "openplan", "openorganisatie"],
     "apis": ["ZGW API's", "Klantinteracties", "Objecten", "Objecttypen", "Verzoeken/Taken/Berichten"]},
    {"id": "notificeren", "naam": "Systemen op de hoogte houden en de inwoner berichten",
     "componenten": ["opennotificaties", "omc"],
     "apis": ["Notificaties", "NotifyNL"]},
    {"id": "archiveren", "naam": "Archiveren en vernietigen",
     "componenten": ["openarchiefbeheer"],
     "apis": ["ZGW Zaken", "Selectielijst"]},
    {"id": "inrichten", "naam": "Zaaktypen en catalogi beheren",
     "componenten": ["openbeheer"],
     "apis": ["ZGW Catalogi", "Referentielijsten"]},
    {"id": "autorisatie", "naam": "Wie mag welk zaaktype zien",
     "componenten": ["pabc"],
     "apis": ["ZGW Autorisaties"]},
]

# component-id in stack.yaml -> naam in landschap.json
LANDSCHAP = {
    "openzaak": "OpenZaak", "opennotificaties": "OpenNotificaties",
    "openobject": "Objecten (Objects API / Open Object)", "objecttypen": "Objecttypen",
    "openklant": "OpenKlant", "openproduct": "OpenProduct",
    "referentielijsten": "Referentielijsten", "selectielijst": "VNG-Selectielijst",
    "openvtb": "Open VTB (Verzoeken, Taken, Berichten)",
    "openformulieren": "Open Formulieren", "openinwoner": "Open Inwoner",
    "openarchiefbeheer": "Open Archiefbeheer", "openbeheer": "OpenBeheer",
    "kiss": "KISS (Klantinteractie-Servicesysteem)",
    "ita": "ITA (Interne Taakafhandeling / Contactverzoek)",
    "pabc": "PABC (Platform Autorisatie Beheer Component)",
    "omc": "NotifyNL OMC (Output Management Component)", "zac": "ZAC (Zaakafhandelcomponent)",
    "nlportal": "NL Portal", "gzac": "Valtimo / GZAC",
    "iko": "IKO (Integraal Klant- en Objectbeeld)", "openorganisatie": "OpenOrganisatie",
    "publicatiebank": "GPP-publicatiebank", "operaton": "Operaton",
    "operaton-modeler": "Operaton Modeler", "openplan": "OpenPlan", "openpdc": "OpenPDC",
    "openpub": "OpenPub", "openregister": "OpenRegister",
    "openfsc": "OpenFSC (Inway, Outway, Manager, Directory)", "openftv": "OpenFTV",
    "keycloak": "Keycloak (identity broker)", "zaakbrug": "ZaakBrug",
    "frank-gateway": "Frank!Gateway (APISIX) in PodiumD",
}


def laad_yaml(naam):
    return yaml.safe_load((ROOT / "stacks" / naam / "stack.yaml").read_text())


def manifest(naam):
    """stack.yaml met basis en erft samengevoegd, zoals tests/ het doet."""
    m = laad_yaml(naam)
    lagen = [laad_yaml("basis")]
    if m.get("erft"):
        lagen.append(laad_yaml(m["erft"]))
    lagen.append(m)
    zonder = set(m.get("zonder") or [])
    comps, gepland = {}, {}
    for laag in lagen:
        for c in laag.get("componenten") or []:
            comps[c["id"]] = {**comps.get(c["id"], {}), **c}
        for c in laag.get("gepland") or []:
            gepland[c["id"]] = c
    for z in zonder:
        comps.pop(z, None)
    return m, list(comps.values()), list(gepland.values())


def images(result, services):
    alles = (result.get("omgeving") or {}).get("services") or {}
    return sorted({alles[s]["image"] for s in services or [] if s in alles})


def main():
    landschap = {c["naam"]: c for c in
                 json.loads((ROOT / "docs/landschap/landschap.json").read_text())["componenten"]}
    uit = {"bron": "lab/ van joepio/demostack; gegenereerd door tools/stackevaluatie.py",
           "gemeten": "7 en 8 oktober 2026, 15 GB geheugen, 4 CPU's, lege volumes",
           "stacks": []}
    for naam in STACKS:
        m, comps, gepland = manifest(naam)
        result = json.loads((ROOT / "results" / f"{naam}.json").read_text())
        componenten = []
        for c in comps:
            l = landschap.get(LANDSCHAP.get(c["id"], ""), {})
            componenten.append({
                "id": c["id"], "naam": c["naam"], "rol": c.get("rol"),
                "images": images(result, c.get("services")),
                "licentie": l.get("licentie"), "maker": l.get("maker_beheerder"),
                "api_standaarden": l.get("api_standaarden"), "repo": l.get("repo_url"),
            })
        licenties = sorted({c["licentie"] for c in componenten if c["licentie"]})
        uit["stacks"].append({
            "id": naam, "titel": m.get("titel", naam), "omschrijving": OMSCHRIJVING[naam],
            "footprint": FOOTPRINT[naam],
            "tests": {"samenvatting": result["samenvatting"],
                      "per_categorie": result["per_categorie"],
                      "afgeleid": result.get("afgeleid")},
            "bekende_fouten": [{"check": c["naam"], "uitleg": c["bekend"]}
                               for c in result["checks"]
                               if c["status"] == "fail" and c.get("bekend")],
            "licenties": licenties,
            "componenten": componenten,
            "niet_draaiend": [{"naam": g["naam"], "reden": g.get("opmerking")} for g in gepland],
        })
    # Vergelijking per functie: per functie en per stack de componenten die het doen.
    # "status" is getest (draait in het lab) of gepland (hoort bij het landschap, draait
    # niet in het lab; ZAC draait wel in de live omgeving op demostack.nl).
    uit["functies"] = []
    for f in FUNCTIES:
        rij = {"id": f["id"], "naam": f["naam"], "apis": f["apis"], "per_stack": {}}
        for s in uit["stacks"]:
            draait = {c["id"]: c["naam"] for c in s["componenten"]}
            gepl = {g["id"]: g["naam"] for g in manifest(s["id"])[2]}
            rij["per_stack"][s["id"]] = (
                [{"naam": draait[i], "status": "getest"} for i in f["componenten"] if i in draait]
                + [{"naam": gepl[i], "status": "gepland"} for i in f["componenten"] if i in gepl])
        uit["functies"].append(rij)
    pad = ROOT / "docs" / "stacks.json"
    pad.write_text(json.dumps(uit, ensure_ascii=False, indent=2) + "\n")
    print(f"{pad.relative_to(ROOT)}: {len(uit['stacks'])} stacks")


if __name__ == "__main__":
    main()
