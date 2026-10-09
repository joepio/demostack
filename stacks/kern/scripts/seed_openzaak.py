"""Maakt een demo-catalogus met zaaktype 'Melding openbare ruimte' in Open Zaak (idempotent-ish)."""
import os, sys, time, jwt, requests

BASE = f"https://zaken.{os.environ['BASE_DOMAIN']}"
CID, SECRET = "demo", os.environ["OZ_DEMO_SECRET"]
RSIN = "002220647"
SL = "https://selectielijst.openzaak.nl/api/v1"

def headers():
    tok = jwt.encode({"iss": CID, "iat": int(time.time()), "client_id": CID,
                      "user_id": "seed", "user_representation": "seed"}, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {tok}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}

def call(method, path, **kw):
    url = path if path.startswith("http") else f"{BASE}/catalogi/api/v1/{path}"
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
existing = call("GET", "zaaktypen", params={"catalogus": cat["url"], "identificatie": "MOR", "status": "alles"})["results"]
for z in existing:
    if z["concept"]:
        call("DELETE", z["url"]); print("concept opgeruimd", z["url"])
    else:
        print("zaaktype bestaat al", z["url"]); sys.exit(0)

proc = requests.get(f"{SL}/procestypen", params={"jaar": 2020}, timeout=30).json()
procestype = next(p for p in proc if p["nummer"] == 11)  # Behandelen van een melding
resultaten = requests.get(f"{SL}/resultaten", params={"procesType": procestype["url"]}, timeout=30).json()["results"]
resultaat = next(r for r in resultaten if r.get("waardering") == "vernietigen" and r.get("procestermijn") != "bestaansduur_procesobject")
omschr = requests.get(f"{SL}/resultaattypeomschrijvingen", timeout=30).json()
afgehandeld = next(o for o in omschr if o["omschrijving"].lower() == "afgehandeld")

iots = [i for i in call("GET", "informatieobjecttypen", params={"catalogus": cat["url"]})["results"] if i["omschrijving"] == "Bijlage melding"]
iot = iots[0] if iots else None
if not iot:
  iot = call("POST", "informatieobjecttypen", json={
    "catalogus": cat["url"], "omschrijving": "Bijlage melding", "vertrouwelijkheidaanduiding": "openbaar",
    "beginGeldigheid": "2026-01-01", "informatieobjectcategorie": "Bijlage"})
  call("POST", iot["url"] + "/publish")

zt = call("POST", "zaaktypen", json={
    "identificatie": "MOR", "omschrijving": "Melding openbare ruimte", "vertrouwelijkheidaanduiding": "openbaar",
    "doel": "Meldingen over de openbare ruimte afhandelen", "aanleiding": "Een inwoner doet een melding",
    "indicatieInternOfExtern": "extern", "handelingInitiator": "Melden", "onderwerp": "Openbare ruimte",
    "handelingBehandelaar": "Afhandelen", "doorlooptijd": "P14D", "opschortingEnAanhoudingMogelijk": False,
    "verlengingMogelijk": False, "publicatieIndicatie": False, "productenOfDiensten": [],
    "referentieproces": {"naam": "Melding openbare ruimte"}, "verantwoordelijke": "Demogemeente",
    "selectielijstProcestype": procestype["url"],
    "catalogus": cat["url"], "besluittypen": [], "gerelateerdeZaaktypen": [], "informatieobjecttypen": [],
    "beginGeldigheid": "2026-01-01", "versiedatum": "2026-01-01"})

for nr, (oms, toel) in enumerate([("Ontvangen", "De melding is ontvangen"),
                                  ("In behandeling", "De melding wordt behandeld"),
                                  ("Afgehandeld", "De melding is afgehandeld")], start=1):
    call("POST", "statustypen", json={"zaaktype": zt["url"], "omschrijving": oms, "volgnummer": nr,
                                     "statustekst": toel, "informeren": nr > 1})
call("POST", "roltypen", json={"zaaktype": zt["url"], "omschrijving": "Melder", "omschrijvingGeneriek": "initiator"})
call("POST", "roltypen", json={"zaaktype": zt["url"], "omschrijving": "Behandelaar", "omschrijvingGeneriek": "behandelaar"})
call("POST", "resultaattypen", json={
    "zaaktype": zt["url"], "omschrijving": "Afgehandeld", "resultaattypeomschrijving": afgehandeld["url"],
    "selectielijstklasse": resultaat["url"], "archiefnominatie": "vernietigen", "archiefactietermijn": "P1Y",
    "brondatumArchiefprocedure": {"afleidingswijze": "afgehandeld", "datumkenmerk": "", "einddatumBekend": False,
                                  "objecttype": "", "registratie": "", "procestermijn": None}})
call("POST", "zaaktype-informatieobjecttypen", json={"zaaktype": zt["url"], "informatieobjecttype": iot["url"],
                                                     "volgnummer": 1, "richting": "inkomend"})
call("POST", zt["url"] + "/publish")
print("klaar:", zt["url"])
