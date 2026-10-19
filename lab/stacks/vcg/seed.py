"""Testdata en inrichting voor stack "vcg", na de gedeelde seed (seed/seed.py). Idempotent.

Samenhang zoals een gemeente met de VCG-basisset die zou hebben:

1. Open Organisatie: afdelingen, teams en de medewerkers van Voorbeeldstad. Dezelfde
   medewerkers (mdw-0101 ...) zijn behandelaar op de geseede zaken en kunnen inloggen in
   Keycloak-realm "vcg".
2. GPP-publicatiebank: Gemeente Voorbeeldstad als organisatie en twee Woo-publicaties
   met een PDF; de documenten staan in de Documenten API van Open Zaak.
3. Operaton: gebruikers en groepen (team Parkeren) en een lopende procesinstantie
   "Parkeervergunning behandelen" voor een nieuwe zaak van testburger D (Jeroen Altena).
   De procesworker zet de zaak in Open Zaak op "In behandeling".
4. OpenPlan, OpenPDC/OpenPub (WordPress), OpenRegister en OpenFSC: zie de functies
   verderop; elk deel slaat zichzelf over als het component niet in de stack draait.

Gebruik (via scripts/stack.sh seed vcg): python stacks/vcg/seed.py
"""
import datetime
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "seed"))

from lib import ApiFout, Client, env, maak_pdf, open_zaak_beheer  # noqa: E402

OPENORGANISATIE = os.environ.get("URL_OPENORGANISATIE", "http://openorganisatie.local:8000")
PUBLICATIEBANK = os.environ.get("URL_PUBLICATIEBANK", "http://publicatiebank.local:8000")
OPERATON = os.environ.get("URL_OPERATON", "http://operaton.local:8080/engine-rest")
OPENPLAN = os.environ.get("URL_OPENPLAN", "http://openplan.local:8000")

ZRC = "zaken/api/v1"
CAT = "catalogi/api/v1"

# Testburger D (zelfde als in stack g4): de procesinstantie in Operaton hoort bij een
# eigen zaak, zodat de vaste verwachtingen voor A, B en C (precies hun seedzaken) blijven.
BURGER_D = "999991991"
ZAAK_OPERATON = "VBS-2026-000110"

AFDELINGEN = [
    # identificatie, naam, verkorte naam, omschrijving
    ("VBS-PO", "Publiekszaken en Omgeving", "P&O", "Vergunningen, parkeren en de buitendienst"),
    ("VBS-SD", "Sociaal Domein", "SD", "Wmo, jeugd en participatie"),
    ("VBS-BV", "Bedrijfsvoering", "BV", "Informatievoorziening en functioneel beheer"),
]
TEAMS = [
    # naam, omschrijving
    ("Vergunningen", "Behandelt omgevingsvergunningen"),
    ("Buitendienst", "Meldingen openbare ruimte"),
    ("Wmo", "Maatwerkvoorzieningen Wmo"),
    ("Parkeren", "Parkeervergunningen bewoners en bedrijven"),
    ("Functioneel beheer", "Beheer van zaaktypen, organisatie en publicaties"),
]
# medewerkerId, voornaam, achternaam, e-mail, team; de eerste vier zijn de behandelaars
# uit seed/data.py (MEDEWERKERS), met dezelfde gebruikersnaam als in Keycloak-realm vcg
MEDEWERKERS = [
    ("mdw-0101", "Anouk", "Vermeulen", "a.vermeulen", "Vergunningen"),
    ("mdw-0202", "Sander", "Bakker", "s.bakker", "Buitendienst"),
    ("mdw-0303", "Rachid", "van Dijk", "r.vandijk", "Wmo"),
    ("mdw-0404", "Lotte", "Smits", "l.smits", "Parkeren"),
    ("mdw-0900", "Mirjam", "de Vos", "beheer.devos", "Functioneel beheer"),
]


def log(msg):
    print(msg, flush=True)


def bereikbaar(url):
    try:
        requests.get(url, timeout=5)
        return True
    except requests.RequestException:
        return False


# ------------------------------------------------------- Open Organisatie
def open_organisatie():
    if not bereikbaar(OPENORGANISATIE):
        log("Open Organisatie draait niet: overgeslagen")
        return
    oo = Client(f"{OPENORGANISATIE}/organisatie/api/v0",
                lambda: {"Authorization": f"Token {env('OPENORGANISATIE_BEHEER_TOKEN')}"}, "Open Organisatie")
    bestaand = {e["identificatie"]: e for e in oo.lijst("organisatorische-eenheid")}
    for ident, naam, kort, oms in AFDELINGEN:
        if ident not in bestaand:
            oo.post("organisatorische-eenheid", {"identificatie": ident, "naam": naam, "verkorteNaam": kort,
                                                 "soortOrganisatie": "afdeling", "omschrijving": oms,
                                                 "emailadres": f"{kort.lower().replace('&', '')}@voorbeeldstad.example"})
    teams = {t["naam"]: t for t in oo.lijst("teams")}
    for naam, oms in TEAMS:
        if naam not in teams:
            teams[naam] = oo.post("teams", {"naam": naam, "omschrijving": oms})
    medewerkers = {m["medewerkerId"]: m for m in oo.lijst("medewerkers")}
    for mid, voor, achter, gebruiker, team in MEDEWERKERS:
        gegevens = {"medewerkerId": mid, "voornaam": voor, "achternaam": achter,
                    "emailadres": f"{gebruiker}@voorbeeldstad.example", "telefoonnummer": "14 0999",
                    "teamsUuids": [teams[team]["uuid"]]}
        if mid in medewerkers:
            huidig = medewerkers[mid]
            if [t["uuid"] for t in huidig.get("teams", [])] != gegevens["teamsUuids"]:
                oo.patch(huidig["url"], {"teamsUuids": gegevens["teamsUuids"]})
        else:
            oo.post("medewerkers", gegevens)
    log(f"Open Organisatie: {len(AFDELINGEN)} afdelingen, {len(TEAMS)} teams, {len(MEDEWERKERS)} medewerkers")


# ----------------------------------------------------- GPP-publicatiebank
PUBLICATIES = [
    {
        "officieleTitel": "Besluit parkeerregulering binnenstad Voorbeeldstad 2026",
        "verkorteTitel": "Parkeerregulering binnenstad 2026",
        "omschrijving": "Het college stelt de parkeertarieven en het vergunninggebied voor de binnenstad vast.",
        "categorie": "beschikking",
        "document": ("besluit-parkeerregulering-2026.pdf", "Besluit parkeerregulering binnenstad 2026", [
            "Gemeente Voorbeeldstad (fictief)",
            "Het college van burgemeester en wethouders besluit:",
            "1. Het vergunninggebied binnenstad loopt van de Havenkade tot de Stationsweg.",
            "2. Een bewonersvergunning kost 120 euro per jaar.",
            "Dit document bevat geen persoonsgegevens.",
        ]),
    },
    {
        "officieleTitel": "Raadsinformatiebrief voortgang Common Ground Voorbeeldstad",
        "verkorteTitel": "Voortgang Common Ground",
        "omschrijving": "Stand van zaken van de overstap naar de componenten van de VCG-basisset.",
        "categorie": "vergaderstuk decentrale overheid",
        "document": ("rib-common-ground.pdf", "Raadsinformatiebrief Common Ground", [
            "Gemeente Voorbeeldstad (fictief)",
            "De registers draaien op Open Zaak, Open Klant en Open Object.",
            "Processen lopen via Operaton; publicaties via de GPP-publicatiebank.",
        ]),
    },
]


def publicatiebank():
    if not bereikbaar(PUBLICATIEBANK):
        log("GPP-publicatiebank draait niet: overgeslagen")
        return
    audit = {"Audit-User-ID": "demogemeente-seed", "Audit-User-Representation": "Seed demogemeente",
             "Audit-Remarks": "testdata stack vcg"}
    gpp = Client(f"{PUBLICATIEBANK}/api/v2",
                 lambda: {"Authorization": f"Token {env('PUBLICATIEBANK_BEHEER_TOKEN')}", **audit}, "GPP-publicatiebank")
    naam = env("GEMEENTE_NAAM")
    org = next((o for o in gpp.lijst("organisaties", naam=naam) if o["naam"] == naam), None)
    if not org:
        org = gpp.post("organisaties", {"naam": naam, "isActief": True})
    categorieen = gpp.lijst("informatiecategorieen")
    bestaand = {p["officieleTitel"]: p for p in gpp.lijst("publicaties", pageSize=100)}
    for spec in PUBLICATIES:
        if spec["officieleTitel"] in bestaand and bestaand[spec["officieleTitel"]]["publicatiestatus"] == "gepubliceerd":
            continue
        ic = next(c for c in categorieen if c["naam"].lower() == spec["categorie"].lower()
                  or c["naam"].lower().startswith(spec["categorie"].lower()))
        pub = bestaand.get(spec["officieleTitel"]) or gpp.post("publicaties", {
            "publicatiestatus": "concept", "officieleTitel": spec["officieleTitel"],
            "verkorteTitel": spec["verkorteTitel"], "omschrijving": spec["omschrijving"],
            "informatieCategorieen": [ic["uuid"]], "publisher": org["uuid"],
            "eigenaar": {"identifier": "beheer.devos", "weergaveNaam": "Mirjam de Vos"},
        })
        docs = gpp.lijst("documenten", publicatie=pub["uuid"])
        if not docs:
            bestand, titel, regels = spec["document"]
            pdf = maak_pdf(titel, regels)
            doc = gpp.post("documenten", {
                "publicatie": pub["uuid"], "officieleTitel": titel, "creatiedatum": datetime.date.today().isoformat(),
                "bestandsformaat": "application/pdf", "bestandsnaam": bestand, "bestandsomvang": len(pdf),
                "aanleveringBestand": "ontvangen",
            })
            positie = 0
            for deel in doc["bestandsdelen"]:
                stuk = pdf[positie:positie + deel["omvang"]]
                positie += deel["omvang"]
                r = requests.put(deel["url"].replace("http://localhost:8252", PUBLICATIEBANK), timeout=60,
                                 headers={"Authorization": f"Token {env('PUBLICATIEBANK_BEHEER_TOKEN')}", **audit},
                                 files={"inhoud": (bestand, stuk, "application/octet-stream")})
                if r.status_code not in (200, 204):
                    raise ApiFout(f"bestandsdeel uploaden: {r.status_code} {r.text[:500]}")
            # Bij een PDF haalt een achtergrondtaak eerst de metadata weg (document in Open
            # Zaak opnieuw aanmaken); pas daarna is de upload voltooid. Wie eerder publiceert,
            # botst met die taak (ConcurrentTransition) en houdt een document zonder inhoud.
            for _ in range(60):
                if gpp.get(f"documenten/{doc['uuid']}").get("uploadVoltooid"):
                    break
                time.sleep(1)
            else:
                raise ApiFout(f"upload van {bestand} niet voltooid binnen 60s")
        gpp.patch(f"publicaties/{pub['uuid']}", {"publicatiestatus": "gepubliceerd"})
    log(f"GPP-publicatiebank: organisatie {naam}, {len(PUBLICATIES)} publicaties met document (Open Zaak)")


# ---------------------------------------------------------------- Operaton
def operaton():
    if not bereikbaar(OPERATON.rsplit("/", 1)[0]):
        log("Operaton draait niet: overgeslagen")
        return
    auth = (env("ADMIN_USERNAME"), env("ADMIN_PASSWORD"))
    s = requests.Session()
    s.auth = auth

    def op(methode, pad, verwacht=(200, 204), **kw):
        r = s.request(methode, f"{OPERATON}/{pad}", timeout=30, **kw)
        if r.status_code not in verwacht:
            raise ApiFout(f"Operaton {methode} {pad} -> {r.status_code}: {r.text[:500]}")
        return r.json() if r.content else None

    # Groepen en gebruikers (zelfde gebruikersnamen als Keycloak-realm vcg)
    for gid, naam in (("parkeren", "Team Parkeren"), ("behandelaars", "Behandelaars")):
        if op("GET", f"group/{gid}", verwacht=(200, 404)).get("id") is None:
            op("POST", "group/create", json={"id": gid, "name": naam, "type": "WORKFLOW"})
    wachtwoord = env("MEDEWERKER_WACHTWOORD")
    for mid, voor, achter, gebruiker, team in MEDEWERKERS[:4]:
        if op("GET", f"user/{gebruiker}/profile", verwacht=(200, 404)).get("id") is None:
            op("POST", "user/create", json={
                "profile": {"id": gebruiker, "firstName": voor, "lastName": achter,
                            "email": f"{gebruiker}@voorbeeldstad.example"},
                "credentials": {"password": wachtwoord}})
        groepen = ["behandelaars"] + (["parkeren"] if team == "Parkeren" else [])
        lid_van = {g["id"] for g in op("GET", "group", params={"member": gebruiker})}
        for g in set(groepen) - lid_van:
            op("PUT", f"group/{g}/members/{gebruiker}", verwacht=(200, 204))
    # Rechten: Tasklist openen en taken van de eigen groep zien en afronden
    bestaande = op("GET", "authorization", params={"groupIdIn": "behandelaars"}) or []
    # resourceType: 0 applicatie, 5 filter, 6 procesdefinitie, 7 taak, 8 procesinstantie
    nodig = [(0, "*", ["ACCESS"]), (5, "*", ["READ"]),
             (6, "*", ["READ", "READ_HISTORY", "READ_INSTANCE", "READ_TASK", "UPDATE_TASK"]),
             (7, "*", ["READ", "UPDATE"]), (8, "*", ["READ"])]
    for rtype, rid, perms in nodig:
        if not any(a["resourceType"] == rtype and a["resourceId"] == rid for a in bestaande):
            op("POST", "authorization/create", json={"type": 1, "permissions": perms, "groupId": "behandelaars",
                                                     "resourceType": rtype, "resourceId": rid})

    zaak = zaak_voor_operaton()
    lopend = op("GET", "process-instance", params={"businessKey": ZAAK_OPERATON})
    historisch = op("GET", "history/process-instance", params={"processInstanceBusinessKey": ZAAK_OPERATON})
    if not lopend and not historisch:
        op("POST", "process-definition/key/parkeervergunning-behandelen/start", json={
            "businessKey": ZAAK_OPERATON,
            "variables": {"zaakUrl": {"value": zaak["url"], "type": "String"},
                          "zaakIdentificatie": {"value": ZAAK_OPERATON, "type": "String"}}})
        log(f"Operaton: proces gestart voor zaak {ZAAK_OPERATON}")
    # Wacht tot de worker de eerste externe taak heeft uitgevoerd
    for _ in range(30):
        taken = op("GET", "task", params={"processInstanceBusinessKey": ZAAK_OPERATON})
        if taken or historisch:
            break
        time.sleep(2)
    log(f"Operaton: groepen parkeren en behandelaars, 4 gebruikers, proces voor {ZAAK_OPERATON} "
        f"({'taak ' + taken[0]['name'] if taken else 'nog geen gebruikerstaak'})")


def zaak_voor_operaton():
    """Aanvraag parkeervergunning van burger D, status Ontvangen (de rest doet het proces)."""
    oz = open_zaak_beheer()
    bestaand = oz.eerste(f"{ZRC}/zaken", identificatie=ZAAK_OPERATON)
    if bestaand:
        return bestaand
    zaaktypen = [z for z in oz.lijst(f"{CAT}/zaaktypen") if z["identificatie"] == "VBS-PARKVERG" and not z["concept"]]
    zt = zaaktypen[0]
    vandaag = datetime.date.today().isoformat()
    zaak = oz.post(f"{ZRC}/zaken", {
        "identificatie": ZAAK_OPERATON, "bronorganisatie": env("GEMEENTE_RSIN"),
        "verantwoordelijkeOrganisatie": env("GEMEENTE_RSIN"), "zaaktype": zt["url"],
        "omschrijving": "Aanvraag parkeervergunning bewoners (Operaton)", "startdatum": vandaag,
        "registratiedatum": vandaag, "vertrouwelijkheidaanduiding": "zaakvertrouwelijk",
    })
    roltypen = oz.lijst(f"{CAT}/roltypen", zaaktype=zt["url"])
    initiator = next(r for r in roltypen if r["omschrijvingGeneriek"] == "initiator")
    oz.post(f"{ZRC}/rollen", {"zaak": zaak["url"], "betrokkeneType": "natuurlijk_persoon",
                              "roltype": initiator["url"], "roltoelichting": "aanvrager",
                              "betrokkeneIdentificatie": {"inpBsn": BURGER_D, "geslachtsnaam": "Altena",
                                                          "voornamen": "Jeroen"}})
    st = sorted(oz.lijst(f"{CAT}/statustypen", zaaktype=zt["url"]), key=lambda s: s["volgnummer"])[0]
    oz.post(f"{ZRC}/statussen", {"zaak": zaak["url"], "statustype": st["url"],
                                 "datumStatusGezet": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                 "statustoelichting": st.get("statustekst", "")})
    log(f"Open Zaak: zaak {ZAAK_OPERATON} (parkeervergunning, burger D) aangemaakt")
    return zaak


# ---------------------------------------------------------------- OpenPlan
# Plannen in het sociaal domein (werk en inkomen): per inwoner een plan met een doel en
# een instrument. Verwijzingen zijn URN's, zoals de Plannen API vraagt: zaken met
# het voorvoegsel urn:nl:gemeenten:zaak:<zaaknummer>, medewerkers uit
# Open Organisatie, personen met hun BSN. Plantypen, doeltypen en instrumenttypen zijn in
# OpenPlan 0.1.0 vaste keuzelijsten (pip/werk/inkomen, hoofddoel/subdoel,
# training/coaching/financiele_ondersteuning).
PLANNEN = [
    # bsn, naam, zaaknummer, medewerker, plantype, plan, doel, instrumenttype, instrument
    ("999993409", "Thea Kouwenhoven", "VBS-2026-000105", "mdw-0303", "inkomen", "Grip op geldzaken",
     "Vaste lasten op tijd betalen", "financiele_ondersteuning", "Budgetbeheer via de gemeente"),
    ("999997609", "Eleonora de Crooy", "VBS-2026-000104", "mdw-0303", "werk", "Terug naar werk",
     "Twintig uur per week aan het werk", "coaching", "Jobcoach via het werkgeversservicepunt"),
]


def openplan():
    if not bereikbaar(OPENPLAN):
        log("OpenPlan draait niet: overgeslagen")
        return
    op = Client(f"{OPENPLAN}/plannen/api/v0", lambda: {"Authorization": f"Token {env('OPENPLAN_BEHEER_TOKEN')}"},
                "OpenPlan")

    def zorg(pad, sleutel, waarde, gegevens):
        for item in op.lijst(pad):
            if item.get(sleutel) == waarde:
                return item
        return op.post(pad, gegevens)

    nu = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    categorie = zorg("doelcategorie", "naam", "Participatie", {"naam": "Participatie"})
    doeltype = zorg("doeltype", "doelType", "hoofddoel", {"doelType": "hoofddoel", "categorieenUuids": [categorie["uuid"]]})
    personen = {p.get("bsn"): p for p in op.lijst("persoon")}
    for bsn, naam, zaaknr, mdw, ptype, plantitel, doeltitel, itype, instrumenttitel in PLANNEN:
        medewerker = f"urn:nld:voorbeeldstad:medewerker:{mdw}"
        plantype = zorg("plantype", "type", ptype, {"type": ptype})
        instrumenttype = zorg("instrumenttype", "instrumentType", itype, {"instrumentType": itype, "categorieenUuids": []})
        persoon = personen.get(bsn) or op.post("persoon", {
            "bsn": bsn, "persoonsprofiel": f"urn:nld:brp:bsn:{bsn}",
            "klant": f"urn:nld:voorbeeldstad:klant:bsn:{bsn}"})
        overkoepelend = zorg("overkoepelendplan", "titel", f"Ondersteuning {naam}",
                             {"titel": f"Ondersteuning {naam}", "status": "actief", "medewerker": medewerker})
        plan = zorg("plan", "titel", plantitel, {
            "titel": plantitel, "status": "actief", "startdatum": nu, "plantypeUuid": plantype["uuid"],
            "overkoepelendPlanUuid": overkoepelend["uuid"], "zaak": f"urn:nl:gemeenten:zaak:{zaaknr}",
            "medewerker": medewerker, "notitie": "Fictief plan van de demogemeente."})
        doel = zorg("doel", "titel", doeltitel, {
            "titel": doeltitel, "status": "actief", "startdatum": nu, "doeltypeUuid": doeltype["uuid"],
            "persoonUuid": persoon["uuid"], "plannenUuids": [plan["uuid"]]})
        zorg("instrument", "titel", instrumenttitel, {
            "titel": instrumenttitel, "status": "actief", "startdatum": nu,
            "instrumenttypeUuid": instrumenttype["uuid"], "doelenUuids": [doel["uuid"]],
            "ontwikkelwensenUuids": [], "zaak": f"urn:nl:gemeenten:zaak:{zaaknr}"})
    log(f"OpenPlan: {len(PLANNEN)} plannen (burgers C en B) met doel en instrument")


# ------------------------------------------------------- OpenRegister (Nextcloud)
OPENREGISTER = os.environ.get("URL_OPENREGISTER", "http://openregister.local") + "/index.php/apps/openregister/api"
SPEELPLEKKEN = [
    # naam, wijk, aantal toestellen (fictief, openbare gegevens)
    ("Speeltuin De Vlinder", "Centrum", 7),
    ("Trapveld Molenwijk", "Molenwijk", 2),
    ("Natuurspeelplaats Het Wilgenbos", "Buitenveld", 5),
]


def openregister():
    if not bereikbaar(OPENREGISTER.split("/index.php")[0] + "/status.php"):
        log("OpenRegister: niet bereikbaar, overgeslagen")
        return
    s = requests.Session()
    s.auth = (env("ADMIN_USERNAME"), env("ADMIN_PASSWORD"))
    s.headers.update({"OCS-APIRequest": "true", "Accept": "application/json"})

    def zorg(soort, slug, data):
        r = s.get(f"{OPENREGISTER}/{soort}", params={"_limit": 200}, timeout=30)
        r.raise_for_status()
        for x in r.json().get("results", []):
            if x.get("slug") == slug:
                return x
        r = s.post(f"{OPENREGISTER}/{soort}", json=data, timeout=30)
        if r.status_code >= 400:
            raise ApiFout(f"OpenRegister {soort}: {r.status_code} {r.text[:300]}")
        return r.json()

    schema = zorg("schemas", "speelplek", {
        "title": "Speelplek", "slug": "speelplek", "description": "Openbare speelplek in Voorbeeldstad",
        "properties": {"naam": {"type": "string", "title": "Naam"}, "wijk": {"type": "string", "title": "Wijk"},
                       "toestellen": {"type": "integer", "title": "Aantal speeltoestellen", "minimum": 0}},
        "required": ["naam", "wijk"]})
    zorg("registers", "openbare-ruimte", {
        "title": "Voorbeeldstad openbare ruimte", "slug": "openbare-ruimte",
        "description": "Objecten in de openbare ruimte van Voorbeeldstad (fictief)", "schemas": [schema["id"]]})
    r = s.get(f"{OPENREGISTER}/objects/openbare-ruimte/speelplek", params={"_limit": 100}, timeout=30)
    r.raise_for_status()
    bestaand = {o.get("naam") for o in r.json().get("results", [])}
    for naam, wijk, toestellen in SPEELPLEKKEN:
        if naam not in bestaand:
            r = s.post(f"{OPENREGISTER}/objects/openbare-ruimte/speelplek",
                       json={"naam": naam, "wijk": wijk, "toestellen": toestellen}, timeout=30)
            if r.status_code >= 400:
                raise ApiFout(f"OpenRegister object: {r.status_code} {r.text[:300]}")
    log(f"OpenRegister: register openbare-ruimte, schema speelplek, {len(SPEELPLEKKEN)} speelplekken")


# ------------------------------------------------------- OpenFSC
def openfsc():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import fsc

    if not fsc.beschikbaar() or not bereikbaar("http://manager.brp.fsc.local:8081/health/ready"):
        log("OpenFSC: niet bereikbaar of geen test-PKI, overgeslagen")
        return
    # 1. Dienst bij de controller van de BRP-leverancier, achter de eigen inway
    diensten = fsc.api("brp", "controller", "GET", "/v1/services")["services"]
    if not any(d["name"] == fsc.DIENST for d in diensten):
        inways = []
        for _ in range(30):
            inways = fsc.api("brp", "controller", "GET", "/v1/inways")["inways"]
            if inways:
                break
            time.sleep(2)
        fsc.api("brp", "controller", "POST", "/v1/services", json={
            "name": fsc.DIENST, "endpoint_url": "http://brp-mock.local/haalcentraal/api/brp",
            "inway_address": inways[0]["address"]})
    # 2. Publicatie in de directory (de directory tekent automatisch)
    if not fsc.contracten("brp", "GRANT_TYPE_SERVICE_PUBLICATION"):
        fsc.nieuw_contract("brp", [{
            "type": "GRANT_TYPE_SERVICE_PUBLICATION", "directory": {"peer_id": fsc.DIRECTORY_ID},
            "service": {"peer_id": fsc.BRP_ID, "name": fsc.DIENST, "protocol": "PROTOCOL_TCP_HTTP_1.1"}}])
    # 3. Verbinding aanvragen door Voorbeeldstad voor de eigen outway
    contract, grant = fsc.grant_dienstverbinding()
    if not contract:
        for _ in range(30):
            fsc.api("voorbeeldstad", "manager", "POST", "/v1/peers/sync")
            peers = fsc.api("voorbeeldstad", "manager", "GET", "/v1/peers")["peers"]
            if any(p["id"] == fsc.BRP_ID for p in peers):
                break
            time.sleep(2)
        outway = fsc.api("voorbeeldstad", "controller", "GET", "/v1/outways")["outways"][0]
        fsc.nieuw_contract("voorbeeldstad", [{
            "type": "GRANT_TYPE_SERVICE_CONNECTION",
            "outway": {"peer_id": fsc.VOORBEELDSTAD_ID, "identification": {
                "type": "OUTWAY_IDENTIFICATION_TYPE_PUBLIC_KEY_THUMBPRINT",
                "public_key_thumbprint": outway["public_key_thumbprint"]}},
            "service": {"type": "SERVICE_TYPE_SERVICE", "peer_id": fsc.BRP_ID, "name": fsc.DIENST}}])
        contract, grant = fsc.grant_dienstverbinding()
    # 4. De BRP-leverancier accepteert (tekent) het contract
    for _ in range(30):
        open_ = fsc.api("brp", "manager", "GET", "/v1/contracts/pending")
        hashes = [c.get("hash") or c.get("content_hash") for c in open_.get("pending_contracts", open_.get("contracts", []))]
        if contract["hash"] in hashes:
            fsc.api("brp", "manager", "PUT", f"/v1/contracts/{contract['hash']}/accept")
            break
        contract, grant = fsc.grant_dienstverbinding()
        if contract and contract.get("state") == "CONTRACT_STATE_VALID":
            break
        time.sleep(2)
    for _ in range(30):
        contract, grant = fsc.grant_dienstverbinding()
        if contract["state"] == "CONTRACT_STATE_VALID":
            break
        time.sleep(2)
    log(f"OpenFSC: dienst {fsc.DIENST} gepubliceerd, contract {contract['state']}, grant {grant['hash'][:24]}...")


def main():
    open_organisatie()
    openplan()
    publicatiebank()
    operaton()
    openregister()
    openfsc()


if __name__ == "__main__":
    main()
