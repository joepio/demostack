"""Een open portaaltaak (TaakV2, soort url) voor testinwoner Suzanne, gekoppeld aan haar eerste melding.
Zichtbaar onder "Mijn taken" in NL Portal en Open Inwoner. Idempotent."""
import os, sys, time, uuid, jwt, requests
D = os.environ["BASE_DOMAIN"]; BSN = "999993653"
OT = f"https://objecttypen.{D}/api/v2/objecttypes/{os.environ['TAAK_OT']}"
H = {"Authorization": f"Token {os.environ['OBJ_TOKEN_KISS']}", "Content-Type": "application/json", "Content-Crs": "EPSG:4326"}
r = requests.get(f"https://objecten.{D}/api/v2/objects", headers=H, params={"type": OT, "data_attr": f"identificatie__value__exact__{BSN}"}, timeout=30)
r.raise_for_status()
if r.json()["count"]:
    print("portaaltaak bestaat al"); sys.exit(0)
t = jwt.encode({"iss": "demo", "iat": int(time.time()), "client_id": "demo", "user_id": "demo", "user_representation": "demo"},
               os.environ["OZ_DEMO_SECRET"], algorithm="HS256")
zaken = requests.get(f"https://zaken.{D}/zaken/api/v1/zaken", timeout=30, params={"rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": BSN},
                     headers={"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326"}).json()["results"]
data = {"titel": "Stuur een foto van de losliggende stoeptegel", "status": "open", "soort": "url",
        "url": {"uri": f"https://formulieren.{D}/"}, "identificatie": {"type": "bsn", "value": BSN},
        "verwerker_taak_id": str(uuid.uuid4()), "eigenaar": "demogemeente"}
if zaken:
    data["koppeling"] = {"registratie": "zaak", "value": zaken[-1]["uuid"]}
r = requests.post(f"https://objecten.{D}/api/v2/objects", headers=H, timeout=30, json={"type": OT, "record": {
    "typeVersion": 1, "data": data, "startAt": time.strftime("%Y-%m-%d")}})
if r.status_code >= 400: print(r.status_code, r.text[:600]); sys.exit(1)
print("portaaltaak aangemaakt")
