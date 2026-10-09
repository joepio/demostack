"""Koppelt demodata aan BRP-testpersoon Suzanne Moulin (BSN 999993653): een zaak met status in Open Zaak."""
import os, sys, time, jwt, requests
D = os.environ["BASE_DOMAIN"]; Z = f"https://zaken.{D}"
BSN = "999993653"
def h():
    t = jwt.encode({"iss": "demo", "iat": int(time.time()), "client_id": "demo", "user_id": "seed", "user_representation": "seed"},
                   os.environ["OZ_DEMO_SECRET"], algorithm="HS256")
    return {"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}
def call(m, url, **kw):
    r = requests.request(m, url, headers=h(), timeout=30, **kw)
    if r.status_code >= 400: print(m, url, r.status_code, r.text[:800]); sys.exit(1)
    return r.json() if r.content else None

zt = call("GET", f"{Z}/catalogi/api/v1/zaaktypen", params={"identificatie": "MOR"})["results"][0]
bestaand = call("GET", f"{Z}/zaken/api/v1/zaken", params={"rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": BSN})["results"]
if bestaand: print("bestaat al:", bestaand[0]["identificatie"]); sys.exit(0)
zaak = call("POST", f"{Z}/zaken/api/v1/zaken", json={
    "bronorganisatie": "002220647", "verantwoordelijkeOrganisatie": "002220647", "zaaktype": zt["url"],
    "omschrijving": "Losliggende stoeptegel Dorpsstraat 12", "toelichting": "Tegel steekt 3 cm uit, struikelgevaar.",
    "startdatum": "2026-10-06", "registratiedatum": "2026-10-06", "vertrouwelijkheidaanduiding": "openbaar"})
rt = call("GET", f"{Z}/catalogi/api/v1/roltypen", params={"zaaktype": zt["url"], "omschrijvingGeneriek": "initiator"})["results"][0]
call("POST", f"{Z}/zaken/api/v1/rollen", json={
    "zaak": zaak["url"], "betrokkeneType": "natuurlijk_persoon", "roltype": rt["url"], "roltoelichting": "Melder",
    "betrokkeneIdentificatie": {"inpBsn": BSN, "geslachtsnaam": "Moulin", "voornamen": "Suzanne", "voorletters": "S."}})
st = sorted(call("GET", f"{Z}/catalogi/api/v1/statustypen", params={"zaaktype": zt["url"]})["results"], key=lambda s: s["volgnummer"])
for s_, dt in [(st[0], "2026-10-06T09:15:00Z"), (st[1], "2026-10-07T14:30:00Z")]:
    call("POST", f"{Z}/zaken/api/v1/statussen", json={"zaak": zaak["url"], "statustype": s_["url"], "datumStatusGezet": dt,
                                                    "statustoelichting": s_["omschrijving"]})
print("zaak:", zaak["identificatie"])
