"""Testdata voor stack "maykin", na de gedeelde seed (seed/seed.py). Idempotent.

1. Applicaties in Open Zaak voor Open Formulieren (zaken aanmaken bij de meldingen) en
   Open Inwoner (lezen), met autorisaties per zaaktype.
2. Objecttype "Externe taak" (JSON-schema) en externe taken in Open Object, zoals Open
   Inwoner 2.4 ze toont (schema "generieke dienstverlening", UrlTaak).
3. Taken in Open VTB (Taken API), de takenbron voor portalen (MijnTaken).
4. Formulier "Melding openbare ruimte" in Open Formulieren: DigiD-login, prefill uit de
   BRP, registratie als zaak in Open Zaak.

Gebruik (via scripts/stack.sh seed maykin): python stacks/maykin/seed.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "seed"))

from lib import (  # noqa: E402
    ApiFout,
    env,
    objecttype_url,
    open_klant,
    open_object,
    open_zaak_beheer,
    token_client,
    zorg_voor_objecttype,
)

OPENVTB = os.environ.get("URL_OPENVTB", "http://openvtb.local:8000")
OPENFORMULIEREN = os.environ.get("URL_OPENFORMULIEREN", "http://openformulieren.local:8000")
# Wat de browser van de inwoner ziet (links in taken)
PUBLIEK_OPENFORMULIEREN = f"http://localhost:{os.environ.get('PORT_OPENFORMULIEREN', '8102')}"

OBJECTTYPE_EXTERNE_TAAK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000b1"
ZAAK_URN_BRON = "urn:nld:voorbeeldstad:zaak:zaaknummer"
FORMULIER_SLUG = "melding-openbare-ruimte"

# Taken: (bsn, zaaknummer, titel, toelichting, einddatum, soort)
TAKEN = [
    ("999990627", "VBS-2026-000101", "Aanvullende tekening dakkapel aanleveren",
     "Upload een zijaanzicht van de dakkapel.", "2026-10-28", "url"),
    ("999990627", "VBS-2026-000101", "Leges omgevingsvergunning betalen",
     "Betaal de leges voor uw aanvraag.", "2026-10-21", "betaal"),
    ("999997609", "VBS-2026-000104", "Medische verklaring traplift aanleveren",
     "Stuur de verklaring van uw huisarts mee.", "2026-11-04", "url"),
    ("999990627", "VBS-2026-000102", "Vragenlijst over de afhandeling van uw melding",
     "Vertel ons hoe de melding is afgehandeld.", "2026-10-30", "url"),
]

# Vragen via het portaal (Open Inwoner, "Mijn vragen"): kanaal webformulier
# Open Inwoner 2.4.5 toont een klantcontact alleen als het een "nummer" heeft (bij Open
# Klant: cijfers, hoogstens 10). Zonder nummer verdwijnt de vraag stil (logregel
# "OpenKlant2Question without content").
VRAGEN = [
    ("9000000001", "999990627", "Wanneer wordt de grofvuilpas verstuurd?",
     "Ik ben verhuisd binnen Voorbeeldstad en heb nog geen nieuwe grofvuilpas ontvangen."),
    ("9000000002", "999997609", "Kan de traplift ook in een huurwoning?",
     "Mijn woning is van een woningcorporatie. Moet ik eerst toestemming vragen?"),
]

oz = open_zaak_beheer()


def log(msg):
    print(msg, flush=True)


def zaaktype_urls():
    zaaktypen = {z["identificatie"]: z for z in oz.lijst("catalogi/api/v1/zaaktypen") if not z["concept"]}
    iots = {i["omschrijving"]: i for i in oz.lijst("catalogi/api/v1/informatieobjecttypen") if not i["concept"]}
    return zaaktypen, iots


def zorg_voor_applicatie(client_id, label, autorisaties):
    body = {"clientIds": [client_id], "label": label, "heeftAlleAutorisaties": False, "autorisaties": autorisaties}
    bestaand = oz.eerste("autorisaties/api/v1/applicaties", clientIds=client_id)
    if bestaand:
        oz.put(bestaand["url"], body)
        log(f"applicatie {client_id} bijgewerkt")
    else:
        oz.post("autorisaties/api/v1/applicaties", body)
        log(f"applicatie {client_id} aangemaakt")


def applicaties():
    zaaktypen, iots = zaaktype_urls()
    # Open Formulieren: zaken aanmaken voor meldingen openbare ruimte, met documenten
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
    zorg_voor_applicatie("open-formulieren", "Open Formulieren (meldingen registreren)", of_aut)

    # Open Inwoner: lezen. Zaken tot en met vertrouwelijk (Wmo), documenten tot en met
    # zaakvertrouwelijk (het vertrouwelijke gespreksverslag niet)
    oip_aut = [{"component": "ztc", "scopes": ["catalogi.lezen"]}]
    for zt in zaaktypen.values():
        oip_aut.append({"component": "zrc", "scopes": ["zaken.lezen"], "zaaktype": zt["url"],
                        "maxVertrouwelijkheidaanduiding": "vertrouwelijk"})
    for iot in iots.values():
        oip_aut.append({"component": "drc", "scopes": ["documenten.lezen"], "informatieobjecttype": iot["url"],
                        "maxVertrouwelijkheidaanduiding": "zaakvertrouwelijk"})
    zorg_voor_applicatie("open-inwoner", "Open Inwoner (inwonersportaal, alleen lezen)", oip_aut)


# ------------------------------------------------------------ externe taken
SCHEMA_EXTERNE_TAAK = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "Externe taak (generieke dienstverlening, UrlTaak)",
    "type": "object",
    "required": ["titel", "status", "soort", "verwerker_taak_id", "eigenaar", "identificatie", "url"],
    "properties": {
        "titel": {"type": "string"},
        "status": {"type": "string", "enum": ["open", "afgerond", "verwerkt", "gesloten"]},
        "soort": {"type": "string"},
        "verwerker_taak_id": {"type": "string"},
        "eigenaar": {"type": "string"},
        "toelichting": {"type": "string"},
        "verloopdatum": {"type": "string"},
        "koppeling": {"type": "object"},
        "identificatie": {"type": "object", "required": ["type", "value"],
                          "properties": {"type": {"type": "string"}, "value": {"type": "string"}}},
        "url": {"type": "object", "required": ["uri"], "properties": {"uri": {"type": "string"}}},
    },
}


def objecttype_externe_taak():
    if zorg_voor_objecttype(OBJECTTYPE_EXTERNE_TAAK, "Externe taak", SCHEMA_EXTERNE_TAAK, "Externe taken"):
        log("objecttype-versie gepubliceerd: Externe taak")


def externe_taken(zaken):
    oo = open_object()
    type_url = objecttype_url(OBJECTTYPE_EXTERNE_TAAK)
    bestaand = {o["record"]["data"].get("verwerker_taak_id") for o in oo.lijst("objects", type=type_url)}
    for nr, (bsn, zaaknummer, titel, toelichting, einddatum, _soort) in enumerate(TAKEN, 1):
        taak_id = f"00000000-0000-4000-8000-0000000000{nr:02d}"
        if taak_id in bestaand:
            continue
        oo.post("objects", {"type": type_url, "record": {"typeVersion": 1, "startAt": "2026-10-01", "data": {
            "titel": titel, "status": "open", "soort": "url", "verwerker_taak_id": taak_id,
            "eigenaar": "gemeente", "toelichting": toelichting, "verloopdatum": f"{einddatum}T23:59:00+02:00",
            "koppeling": {"registratie": "zaak", "value": zaken[zaaknummer]["uuid"]},
            "identificatie": {"type": "bsn", "value": bsn},
            "url": {"uri": f"{PUBLIEK_OPENFORMULIEREN}/{FORMULIER_SLUG}"},
        }}}, headers={"Content-Crs": "EPSG:4326"})
        log(f"externe taak aangemaakt (Open Object): {titel}")


# ------------------------------------------------------------------ Open VTB
def openvtb():
    return token_client(f"{OPENVTB}/taken/api/v1", env("OPENVTB_BEHEER_TOKEN"), "Open VTB")


def vtb_taken():
    vtb = openvtb()
    for bsn, zaaknummer, titel, toelichting, einddatum, soort in TAKEN:
        persoon = f"urn:nld:brp:bsn:{bsn}"
        bestaande = vtb.lijst("externetaken", isToegewezenAan=persoon)
        if any(t["titel"] == titel and t.get("isToegewezenAan") == persoon for t in bestaande):
            continue
        body = {
            "titel": titel, "status": "open", "startdatum": "2026-10-01",
            "einddatumHandelingsTermijn": einddatum, "toelichting": toelichting,
            "isToegewezenAan": persoon,
            "isGerelateerdAan": [{"urn": f"{ZAAK_URN_BRON}:{zaaknummer}"}],
        }
        if soort == "betaal":
            body["handelingsPerspectief"] = "betalen"
            body["details"] = {"bedrag": "131.75", "valuta": "EUR", "transactieomschrijving": f"Leges {zaaknummer}",
                               "doelrekening": {"naam": "Gemeente Voorbeeldstad", "code": "VBS-LEGES",
                                                "iban": "NL18BANK0123456789"}}
            vtb.post("betaaltaken", body)
        else:
            body["handelingsPerspectief"] = "informatie_geven"
            body["details"] = {"uitvraagLink": f"{PUBLIEK_OPENFORMULIEREN}/{FORMULIER_SLUG}",
                               "voorinvullenGegevens": {"zaaknummer": zaaknummer}}
            vtb.post("urltaken", body)
        log(f"taak aangemaakt (Open VTB): {titel}")


# ---------------------------------------------------------------- Open Klant
def vragen():
    ok = open_klant()
    for nummer, bsn, onderwerp, inhoud in VRAGEN:
        partij = ok.eerste("partijen", partijIdentificator__objectId=bsn)
        if not partij:
            raise ApiFout(f"geen partij voor {bsn} in Open Klant (gedeelde seed gedraaid?)")
        bestaande = ok.lijst("klantcontacten", hadBetrokkene__wasPartij__uuid=partij["uuid"])
        bestaand = next((k for k in bestaande if k["onderwerp"] == onderwerp), None)
        if bestaand:
            if not bestaand.get("nummer"):
                ok.patch(bestaand["url"], {"nummer": nummer})
            continue
        kc = ok.post("klantcontacten", {
            "nummer": nummer, "kanaal": "webformulier", "onderwerp": onderwerp, "inhoud": inhoud, "indicatieContactGelukt": True,
            "taal": "nld", "vertrouwelijk": False, "plaatsgevondenOp": "2026-10-02T19:40:00+02:00",
        })
        naam = partij["partijIdentificatie"]["contactnaam"]
        ok.post("betrokkenen", {
            "wasPartij": {"uuid": partij["uuid"]}, "hadKlantcontact": {"uuid": kc["uuid"]},
            "rol": "klant", "initiator": True, "organisatienaam": "",
            "contactnaam": {k: naam.get(k, "") for k in ("voorletters", "voornaam", "voorvoegselAchternaam",
                                                          "achternaam")},
        })
        log(f"vraag aangemaakt (Open Klant): {onderwerp}")


# --------------------------------------------------------- Open Formulieren
def openformulieren():
    return token_client(f"{OPENFORMULIEREN}/api/v2", env("OPENFORMULIEREN_BEHEER_TOKEN"), "Open Formulieren")


COMPONENTEN = [
    {"type": "fieldset", "key": "melder", "label": "Uw gegevens", "components": [
        {"type": "textfield", "key": "voornamen", "label": "Voornamen", "disabled": True,
         "prefill": {"plugin": "haalcentraal", "attribute": "naam.voornamen", "identifierRole": "main"}},
        {"type": "textfield", "key": "achternaam", "label": "Achternaam", "disabled": True,
         "prefill": {"plugin": "haalcentraal", "attribute": "naam.geslachtsnaam", "identifierRole": "main"}},
        {"type": "email", "key": "email", "label": "E-mailadres", "validate": {"required": True}},
    ]},
    {"type": "radio", "key": "categorie", "label": "Waar gaat uw melding over?", "validate": {"required": True},
     "openForms": {"dataSrc": "manual"},
     "values": [{"value": "afval", "label": "Afval"}, {"value": "bestrating", "label": "Bestrating"},
                {"value": "verlichting", "label": "Straatverlichting"}, {"value": "groen", "label": "Groen"}]},
    {"type": "textfield", "key": "locatie", "label": "Locatie (straat en huisnummer of omschrijving)",
     "validate": {"required": True}},
    {"type": "textarea", "key": "omschrijving", "label": "Omschrijving", "validate": {"required": True,
                                                                                      "maxLength": 1000}},
]


def formulier():
    of = openformulieren()
    bestaand = next((f for f in of.lijst("forms") if f["slug"] == FORMULIER_SLUG), None)
    if bestaand and bestaand.get("steps"):
        return bestaand
    definitie = next((d for d in of.lijst("form-definitions") if d.get("slug") == FORMULIER_SLUG), None)
    if not definitie:
        definitie = of.post("form-definitions", {
            "name": "Melding openbare ruimte", "slug": FORMULIER_SLUG, "loginRequired": True,
            "configuration": {"display": "form", "components": COMPONENTEN},
        })
    if not bestaand:
        bestaand = of.post("forms", {
            "name": "Melding openbare ruimte",
            "internalName": "Melding openbare ruimte (demogemeente)",
            "slug": FORMULIER_SLUG,
            "active": True,
            "authBackends": [{"backend": "digid_oidc", "options": {}}],
            "registrationBackends": [{
                "key": "zaak", "name": "Zaak in Open Zaak", "backend": "zgw-create-zaak",
                "options": {
                    "zgwApiGroup": zgw_groep_id(),
                    "catalogue": {"domain": "VBSTD", "rsin": env("GEMEENTE_RSIN")},
                    "caseTypeIdentification": "VBS-MOR",
                    "documentTypeDescription": "Melding",
                    "zaakVertrouwelijkheidaanduiding": "openbaar",
                    "objectsApiGroup": None,
                },
            }],
            "submissionAllowed": "yes",
            "explanationTemplate": "<p>Meld een probleem in de openbare ruimte van Voorbeeldstad. "
                                   "Dit is een demo met fictieve gegevens.</p>",
        })
        log("formulier aangemaakt: Melding openbare ruimte")
    of.post(f"forms/{bestaand['uuid']}/steps", {
        "formDefinition": definitie["url"], "index": 0, "slug": "melding",
        "literals": {"previousText": {"value": ""}, "saveText": {"value": ""}, "nextText": {"value": ""}},
    })
    log("formulierstap toegevoegd")
    return of.get(f"forms/{bestaand['uuid']}")


def of_sessie():
    """Beheersessie in Open Formulieren: de endpoints van de registratieplugins
    accepteren alleen sessie-authenticatie, geen API-token."""
    import re

    import requests

    s = requests.Session()
    url = f"{OPENFORMULIEREN}/admin/classic-login/"
    csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', s.get(url, timeout=30).text).group(1)
    r = s.post(url, data={"csrfmiddlewaretoken": csrf, "admin_login_view-current_step": "auth",
                          "auth-username": os.environ.get("ADMIN_USERNAME", "admin"),
                          "auth-password": env("ADMIN_PASSWORD"), "next": "/admin/"},
               headers={"Referer": url}, timeout=30, allow_redirects=False)
    if r.status_code != 302:
        raise ApiFout(f"inloggen in de admin van Open Formulieren mislukt ({r.status_code})")
    return s


def zgw_groep_id():
    s = of_sessie()
    r = s.get(f"{OPENFORMULIEREN}/api/v2/registration/plugins", timeout=30)
    if r.status_code != 200:
        raise ApiFout(f"registratieplugins opvragen gaf {r.status_code}: {r.text[:300]}")
    plugin = next(p for p in r.json() if p["id"] == "zgw-create-zaak")
    keuzes = plugin["schema"]["properties"]["zgwApiGroup"]
    for waarde, label in zip(keuzes["enum"], keuzes.get("enumNames", keuzes["enum"])):
        if "Voorbeeldstad" in str(label):
            return waarde
    return keuzes["enum"][0]


def main():
    log("== Seed stack maykin")
    applicaties()
    objecttype_externe_taak()
    zaken = {z["identificatie"]: z for z in oz.lijst("zaken/api/v1/zaken", bronorganisatie=env("GEMEENTE_RSIN"))}
    externe_taken(zaken)
    vtb_taken()
    vragen()
    formulier()
    log("== Seed stack maykin klaar")


if __name__ == "__main__":
    try:
        main()
    except ApiFout as e:
        print(f"FOUT: {e}", file=sys.stderr)
        sys.exit(1)
