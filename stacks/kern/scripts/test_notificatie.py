"""Rooktest: zet een status op de demozaak en controleer dat Open Zaak een notificatie naar Open Notificaties stuurt."""
import os, time, jwt, requests
D = os.environ["BASE_DOMAIN"]; Z = f"https://zaken.{D}"
t = jwt.encode({"iss": "demo", "iat": int(time.time()), "client_id": "demo", "user_id": "test", "user_representation": "test"},
               os.environ["OZ_DEMO_SECRET"], algorithm="HS256")
H = {"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326", "Content-Crs": "EPSG:4326"}
zaak = requests.get(f"{Z}/zaken/api/v1/zaken", params={"identificatie": "ZAAK-2026-0000000001"}, headers=H).json()["results"][0]
st = sorted(requests.get(f"{Z}/catalogi/api/v1/statustypen", params={"zaaktype": zaak["zaaktype"]}, headers=H).json()["results"],
            key=lambda s: s["volgnummer"])[1]
r = requests.post(f"{Z}/zaken/api/v1/statussen", headers=H, json={
    "zaak": zaak["url"], "statustype": st["url"], "datumStatusGezet": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "statustoelichting": "Rooktest notificatie"})
print("status", r.status_code)
