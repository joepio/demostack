"""Open Product: API-account voor de demo, een thema en producttype parkeervergunning, en voor testinwoner Suzanne
(BSN 999993653) een actieve parkeervergunning, ontstaan uit haar laatste zaak in Open Zaak. Draait in de Django-shell van Open Product (ORM voor het account,
de rest via de eigen API op localhost). Idempotent.
    docker compose exec -T -e OP_TOKEN_DEMO -e OZ_DEMO_SECRET -e BASE_DOMAIN openproduct python src/manage.py shell < scripts/seed_openproduct.py"""
import datetime, os, sys, time
import jwt, requests
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from rest_framework.authtoken.models import Token
from openproduct.producttypen.models import ProductType, UniformeProductNaam
from openproduct.producttypen.models.producttypepermission import PermissionModes, ProductTypePermission

BSN = "999993653"
user, _ = get_user_model().objects.get_or_create(username="demostack-api")
# De API controleert Django-modelrechten; het demo-account mag alles in producttypen en producten
user.user_permissions.set(Permission.objects.filter(content_type__app_label__in=["producttypen", "producten", "locaties"]))
Token.objects.filter(user=user).exclude(key=os.environ["OP_TOKEN_DEMO"]).delete()
Token.objects.get_or_create(user=user, key=os.environ["OP_TOKEN_DEMO"])

# Producttypen voor burgers vragen een naam uit de Uniforme Productnamenlijst (setup.sh laadt de hele lijst;
# zonder internet alleen deze ene naam)
UniformeProductNaam.objects.get_or_create(naam="parkeervergunning",
    defaults={"uri": "http://standaarden.overheid.nl/owms/terms/parkeervergunning"})

API = "http://localhost:8000"
H = {"Authorization": f"Token {os.environ['OP_TOKEN_DEMO']}", "Host": "localhost"}

def lijst(pad, **params):
    r = requests.get(f"{API}{pad}", headers=H, params=params, timeout=30); r.raise_for_status()
    return r.json()["results"]

def maak(pad, data):
    r = requests.post(f"{API}{pad}", headers=H, json=data, timeout=30)
    if r.status_code >= 400: print(pad, r.status_code, r.text[:600]); sys.exit(1)
    print("aangemaakt:", data.get("naam")); return r.json()

T = "/producttypen/api/v1"
thema = next((t for t in lijst(f"{T}/themas") if t["naam"] == "Parkeren"), None) or maak(f"{T}/themas", {
    "naam": "Parkeren", "beschrijving": "Vergunningen en ontheffingen voor parkeren", "gepubliceerd": True,
    "hoofd_thema": None, "producttype_uuids": []})
pt = next((p for p in lijst(f"{T}/producttypen") if p["code"] == "PARKEERVERGUNNING-BEWONER"), None) or maak(f"{T}/producttypen", {
    "code": "PARKEERVERGUNNING-BEWONER", "uniforme_product_naam": "parkeervergunning", "naam": "Parkeervergunning voor bewoners", "doelgroep": "burgers",
    "samenvatting": "Met een bewonersvergunning parkeert u in uw eigen wijk.", "thema_uuids": [thema["uuid"]],
    "toegestane_statussen": ["in_aanvraag", "actief", "verlopen"]})
# Producten vragen daarnaast rechten per producttype
ProductTypePermission.objects.get_or_create(user=user, producttype=ProductType.objects.get(uuid=pt["uuid"]),
    defaults={"mode": PermissionModes.read_and_write})
if not lijst("/producten/api/v1/producten", eigenaren__bsn=BSN):
    # Open Product eist de zaak waaruit het product ontstond
    t = jwt.encode({"iss": "demo", "iat": int(time.time()), "client_id": "demo", "user_id": "demo", "user_representation": "demo"},
                   os.environ["OZ_DEMO_SECRET"], algorithm="HS256")
    zaken = requests.get(f"https://zaken.{os.environ['BASE_DOMAIN']}/zaken/api/v1/zaken", timeout=30,
                         params={"rol__betrokkeneIdentificatie__natuurlijkPersoon__inpBsn": BSN},
                         headers={"Authorization": f"Bearer {t}", "Accept-Crs": "EPSG:4326"}).json().get("results", [])
    if not zaken: print("geen zaak van Suzanne in Open Zaak; product overgeslagen"); sys.exit(0)
    vandaag = datetime.date.today()
    maak("/producten/api/v1/producten", {
        "naam": "Parkeervergunning Suzanne Moulin", "producttype_uuid": pt["uuid"], "status": "actief",
        "start_datum": vandaag.isoformat(), "eind_datum": vandaag.replace(year=vandaag.year + 1).isoformat(),
        "gepubliceerd": True, "eigenaren": [{"bsn": BSN}],
        "aanvraag_zaak_url": zaken[-1]["url"]})
