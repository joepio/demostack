"""Demomeldingen in Open Zaak (idempotent): verschillende soorten, inwoners uit de BRP-testset, locaties en statussen.
Met OPRUIMEN=1 worden eerst de testzaken van rooktests (identificatie OF-...) verwijderd."""
import os, sys, time, jwt, requests
D = os.environ["BASE_DOMAIN"]; Z = f"https://zaken.{D}"
def h():
    t = jwt.encode({"iss": "demo", "iat": int(time.time()), "client_id": "demo", "user_id": "seed", "user_representation": "seed"},
                   os.environ["OZ_DEMO_SECRET"], algorithm="HS256")
    return {"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}
def call(m, url, **kw):
    r = requests.request(m, url, headers=h(), timeout=30, **kw)
    if r.status_code >= 400: print(m, url, r.status_code, r.text[:600]); sys.exit(1)
    return r.json() if r.content else None
def all_pages(url, params):
    out = []
    while url:
        d = call("GET", url, params=params); out += d["results"]; url, params = d.get("next"), None
    return out

if os.environ.get("OPRUIMEN") == "1":
    for z in all_pages(f"{Z}/zaken/api/v1/zaken", {"bronorganisatie": "002220647"}):
        if z["identificatie"].startswith("OF-"):
            call("DELETE", z["url"]); print("opgeruimd", z["identificatie"])

zt = call("GET", f"{Z}/catalogi/api/v1/zaaktypen", params={"identificatie": "MOR"})["results"]
zt = next(x for x in zt if not x.get("eindeGeldigheid"))
st = {s["omschrijving"]: s for s in call("GET", f"{Z}/catalogi/api/v1/statustypen", params={"zaaktype": zt["url"]})["results"]}
rt = {r["omschrijvingGeneriek"]: r for r in call("GET", f"{Z}/catalogi/api/v1/roltypen", params={"zaaktype": zt["url"]})["results"]}

MELDINGEN = [  # soort, plek, toelichting, BSN, voornaam, achternaam, lon, lat, start, statussen
    ("Losliggende stoeptegel", "Dorpsstraat 12", "Tegel steekt 3 cm uit, struikelgevaar voor ouderen bij de bushalte.",
     "999993653", "Suzanne", "Moulin", 5.3872, 52.1561, "2026-10-06", ["Intake", "In behandeling"]),
    ("Kapotte straatverlichting", "Parkweg ter hoogte van nr. 40", "Drie lantaarnpalen achter elkaar branden niet, het fietspad is 's avonds pikdonker.",
     "999991723", "Lukas", "Klamer", 5.3925, 52.1590, "2026-10-07", ["Intake"]),
    ("Zwerfafval", "Speeltuin Molenwijk", "Glasscherven en blikjes bij de zandbak, kinderen spelen er.",
     "999993847", "Merel", "Kooyman", 5.3801, 52.1532, "2026-10-08", ["Intake", "In behandeling", "Wacht op aanvullende informatie"]),
    ("Overhangend groen", "Kerkstraat 8", "Haag hangt over het fietspad, fietsers moeten uitwijken naar de weg.",
     "999995078", "Christina", "Maassen", 5.3890, 52.1575, "2026-10-08", ["Intake"]),
    ("Losliggende stoeptegel", "Marktplein, voor de bakker", "Twee tegels liggen los na de markt van zaterdag.",
     "999990639", "Mattheus", "du Burck", 5.3860, 52.1553, "2026-10-02", ["Intake", "In behandeling", "Afgerond"]),
]
for soort, plek, toel, bsn, vn, an, lon, lat, start, statussen in MELDINGEN:
    oms = f"{soort}: {plek}"
    bestaand = [z for z in call("GET", f"{Z}/zaken/api/v1/zaken",
                params={"rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": bsn})["results"]
                if z["omschrijving"].replace(":", "") == oms.replace(":", "")]
    if bestaand:
        print("bestaat al:", bestaand[0]["identificatie"], oms); continue
    zaak = call("POST", f"{Z}/zaken/api/v1/zaken", json={
        "bronorganisatie": "002220647", "verantwoordelijkeOrganisatie": "002220647", "zaaktype": zt["url"],
        "omschrijving": oms, "toelichting": toel, "startdatum": start, "registratiedatum": start,
        "vertrouwelijkheidaanduiding": "openbaar", "zaakgeometrie": {"type": "Point", "coordinates": [lon, lat]}})
    call("POST", f"{Z}/zaken/api/v1/rollen", json={
        "zaak": zaak["url"], "betrokkeneType": "natuurlijk_persoon", "roltype": rt["initiator"]["url"], "roltoelichting": "Melder",
        "betrokkeneIdentificatie": {"inpBsn": bsn, "geslachtsnaam": an, "voornamen": vn, "voorletters": vn[0] + "."}})
    for i, s in enumerate(statussen):
        if s == "Afgerond":  # eindstatus vraagt eerst een resultaat
            res = next(r for r in call("GET", f"{Z}/catalogi/api/v1/resultaattypen", params={"zaaktype": zt["url"]})["results"]
                       if r["omschrijving"] == "Afgehandeld")
            call("POST", f"{Z}/zaken/api/v1/resultaten", json={"zaak": zaak["url"], "resultaattype": res["url"], "toelichting": "Hersteld"})
        call("POST", f"{Z}/zaken/api/v1/statussen", json={"zaak": zaak["url"], "statustype": st[s]["url"],
             "datumStatusGezet": f"{start}T{9 + i:02d}:00:00Z", "statustoelichting": s})
    print("aangemaakt:", zaak["identificatie"], oms)


