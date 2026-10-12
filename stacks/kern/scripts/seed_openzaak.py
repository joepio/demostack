"""Maakt een demo-catalogus met zaaktype 'Melding openbare ruimte' in Open Zaak (idempotent-ish).
Met CATALOGI_API, ZGW_CLIENT, ZGW_SECRET en SELECTIELIJST_API draait hetzelfde script tegen een andere ZGW-implementatie
(bijvoorbeeld OneGround): zo zie je of beide hetzelfde accepteren."""
import os, sys, time, jwt, requests

CATALOGI = os.environ.get("CATALOGI_API", f"https://zaken.{os.environ['BASE_DOMAIN']}/catalogi/api/v1")
CID = os.environ.get("ZGW_CLIENT", "demo")
SECRET = os.environ.get("ZGW_SECRET") or os.environ["OZ_DEMO_SECRET"]
RSIN = "002220647"
SL = os.environ.get("SELECTIELIJST_API", "https://selectielijst.openzaak.nl/api/v1")

def headers():
    tok = jwt.encode({"iss": CID, "iat": int(time.time()), "client_id": CID,
                      "user_id": "seed", "user_representation": "seed"}, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {tok}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}

def call(method, path, **kw):
    url = path if path.startswith("http") else f"{CATALOGI}/{path}"
    r = requests.request(method, url, headers=headers(), timeout=30, **kw)
    if r.status_code >= 400:
        print(method, url, r.status_code, r.text[:1500]); sys.exit(1)
    return r.json() if r.content else None

cats = call("GET", "catalogussen", params={"domein": "DEMO"})["results"]
if cats:
    cat = cats[0]; print("catalogus bestaat al", cat["url"])
else:
    cat = call("POST", "catalogussen", json={
        "domein": "DEMO", "rsin": RSIN, "naam": "Demogemeente",
        "contactpersoonBeheerNaam": "Functioneel beheer", "contactpersoonBeheerEmailadres": "beheer@demogemeente.local",
        "versie": "1", "begindatumVersie": "2026-01-01"})
import datetime
TODAY = datetime.date.today()
existing = call("GET", "zaaktypen", params={"catalogus": cat["url"], "identificatie": "MOR", "status": "alles"})["results"]
for z in existing:
    if z["concept"]:
        call("DELETE", z["url"]); print("concept opgeruimd", z["url"])
published = [z for z in existing if not z["concept"]]

def statusnamen(z):
    return {s["omschrijving"] for s in call("GET", "statustypen", params={"zaaktype": z["url"]})["results"]}

# De zaaktype-inrichting voldoet aan de eisen van ZAC (statustypen, rollen Initiator/Behandelaar, informatieobjecttype e-mail)
current = [z for z in published if not z.get("eindeGeldigheid")]
if current and "Intake" in statusnamen(current[0]):
    print("zaaktype bestaat al", current[0]["url"]); sys.exit(0)
begin = TODAY.isoformat() if published else "2026-01-01"
if current:  # oude versie afsluiten; de nieuwe versie gaat vandaag in
    call("PATCH", current[0]["url"], json={"eindeGeldigheid": (TODAY - datetime.timedelta(days=1)).isoformat()})
    print("oude versie afgesloten", current[0]["url"])

proc = requests.get(f"{SL}/procestypen", params={"jaar": 2020}, timeout=30).json()
procestype = next(p for p in proc if p["nummer"] == 11)  # Behandelen van een melding
resultaten = requests.get(f"{SL}/resultaten", params={"procesType": procestype["url"]}, timeout=30).json()["results"]
resultaat = next(r for r in resultaten if r.get("waardering") == "vernietigen" and r.get("procestermijn") != "bestaansduur_procesobject")
omschr = requests.get(f"{SL}/resultaattypeomschrijvingen", timeout=30).json()
def omschrijving(naam): return next(o for o in omschr if o["omschrijving"].lower() == naam)

def iot(naam, categorie):
    found = [i for i in call("GET", "informatieobjecttypen", params={"catalogus": cat["url"]})["results"] if i["omschrijving"] == naam]
    if found: return found[0]
    i = call("POST", "informatieobjecttypen", json={
        "catalogus": cat["url"], "omschrijving": naam, "vertrouwelijkheidaanduiding": "openbaar",
        "beginGeldigheid": "2026-01-01", "informatieobjectcategorie": categorie})
    call("POST", i["url"] + "/publish")
    return i
bijlage, email = iot("Bijlage melding", "Bijlage"), iot("e-mail", "E-mail")

zt = call("POST", "zaaktypen", json={
    "identificatie": "MOR", "omschrijving": "Melding openbare ruimte", "vertrouwelijkheidaanduiding": "openbaar",
    "doel": "Meldingen over de openbare ruimte afhandelen", "aanleiding": "Een inwoner doet een melding",
    "indicatieInternOfExtern": "extern", "handelingInitiator": "Melden", "onderwerp": "Openbare ruimte",
    "handelingBehandelaar": "Afhandelen", "doorlooptijd": "P14D", "opschortingEnAanhoudingMogelijk": True,
    "verlengingMogelijk": True, "verlengingstermijn": "P14D", "publicatieIndicatie": False, "productenOfDiensten": [],
    "referentieproces": {"naam": "Melding openbare ruimte"}, "verantwoordelijke": "Demogemeente",
    "selectielijstProcestype": procestype["url"],
    "catalogus": cat["url"], "besluittypen": [], "gerelateerdeZaaktypen": [], "informatieobjecttypen": [], "deelzaaktypen": [],
    "beginGeldigheid": begin, "versiedatum": begin})

for nr, (oms, toel) in enumerate([("Intake", "De melding is ontvangen"),
                                  ("In behandeling", "De melding wordt behandeld"),
                                  ("Wacht op aanvullende informatie", "We wachten op informatie van de melder"),
                                  ("Heropend", "De melding is heropend"),
                                  ("Afgerond", "De melding is afgehandeld")], start=1):
    call("POST", "statustypen", json={"zaaktype": zt["url"], "omschrijving": oms, "volgnummer": nr,
                                     "statustekst": toel, "informeren": nr > 1})
for oms, gen in [("Initiator", "initiator"), ("Behandelaar", "behandelaar"), ("Belanghebbende", "belanghebbende")]:
    call("POST", "roltypen", json={"zaaktype": zt["url"], "omschrijving": oms, "omschrijvingGeneriek": gen})
brondatum = {"afleidingswijze": "afgehandeld", "datumkenmerk": "", "einddatumBekend": False,
             "objecttype": "", "registratie": "", "procestermijn": None}
for oms, rto in [("Afgehandeld", "afgehandeld"), ("Niet ontvankelijk", "afgebroken")]:
    call("POST", "resultaattypen", json={
        "zaaktype": zt["url"], "omschrijving": oms, "resultaattypeomschrijving": omschrijving(rto)["url"],
        "selectielijstklasse": resultaat["url"], "archiefnominatie": "vernietigen", "archiefactietermijn": "P1Y",
        "brondatumArchiefprocedure": brondatum, "besluittypen": []})
for nr, (i, richting) in enumerate([(bijlage, "inkomend"), (email, "uitgaand")], start=1):
    # Catalogi 1.3 verwijst hier met de omschrijving; Open Zaak accepteert ook de URL, OneGround alleen de omschrijving
    ref = i["omschrijving"] if "CATALOGI_API" in os.environ else i["url"]
    call("POST", "zaaktype-informatieobjecttypen", json={"zaaktype": zt["url"], "informatieobjecttype": ref,
                                                         "volgnummer": nr, "richting": richting})
call("POST", zt["url"] + "/publish")
print("klaar:", zt["url"])
