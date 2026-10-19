"""Aanvullende configuratie van Open Inwoner 2.4.5 (stack maykin), idempotent.

Wat setup-configuration van deze versie nog niet kan (latere versies wel):
- CMS-pagina's: homepage met "Mijn zaken" en "Mijn taken", Mijn aanvragen, Mijn profiel,
  Mijn vragen (Open Klant) en Onderwerpen;
- BRP: Haal Centraal BRP Personen 2.0 op de BRP-mock;
- taken: Objecten API en objecttype "Externe taak" (schema generieke dienstverlening);
- siteconfiguratie: naam, kleuren, alleen DigiD-login;
- actor voor "Mijn vragen": zoekt of maakt die in Open Klant.
- beheerder: superuser admin@voorbeeldstad.example met ADMIN_PASSWORD.
Draait in de init-container: `python src/manage.py shell < configureer.py`.
"""
import os

import requests
from cms import api
from cms.models import Page, PageContent, Placeholder
from django.db import transaction
from zgw_consumers.models import Service

from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.extensions.models import CommonExtension
from open_inwoner.cms.plugins.models import TasksConfig
from open_inwoner.cms.products.cms_apps import ProductsApphook
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.tests.cms_tools import create_apphook_page, publish_page
from open_inwoner.configurations.models import SiteConfiguration
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from open_inwoner.openklant.cms_apps import OpenklantApphook
from open_inwoner.openklant.models import OpenKlant2Config
from objectsapiclient.models import ObjectsAPIServiceConfiguration

OBJECTTYPE_EXTERNE_TAAK = "7c1d4a0e-5a7b-4c1e-8f00-0000000000b1"

# ---------------------------------------------------------------- beheerder
from django.contrib.auth import get_user_model

User = get_user_model()
beheerder = User.objects.filter(email="admin@voorbeeldstad.example").first() or User(
    email="admin@voorbeeldstad.example", first_name="Beheer", last_name="Voorbeeldstad")
beheerder.is_staff = beheerder.is_superuser = beheerder.is_active = True
beheerder.set_password(os.environ["ADMIN_PASSWORD"])
beheerder.save()
print("beheerder klaar: admin@voorbeeldstad.example")

# ---------------------------------------------------------------- siteconfiguratie
sc = SiteConfiguration.get_solo()
sc.name = "Mijn Voorbeeldstad"
sc.primary_color = "#1d4f91"
sc.secondary_color = "#e9eef6"
sc.accent_color = "#1d4f91"
sc.login_show = True
sc.login_allow_registration = False
sc.eherkenning_enabled = False
sc.email_verification_required = False
sc.enable_virus_scan = False
sc.home_welcome_title = "Welkom bij Mijn Voorbeeldstad"
sc.home_welcome_intro = "Log in met DigiD om uw zaken, taken en vragen te zien. (Demo met fictieve gegevens.)"
sc.save()
print("siteconfiguratie klaar")

# ---------------------------------------------------------------------- BRP
hc = HaalCentraalConfig.get_solo()
hc.service = Service.objects.get(slug="brp-personen")
hc.brp_version = "2.0"
hc.save()
print("BRP: Haal Centraal BRP Personen 2.0 (BRP-mock)")

# -------------------------------------------------- taken uit Open Object
oc = ObjectsAPIServiceConfiguration.get_solo()
oc.objects_api_client_config = Service.objects.get(slug="objecten-api")
# Open Object 4: Objecten en Objecttypen onder dezelfde api_root. Met losse API's (stack
# dimpact, zoals PodiumD) wijst OIP_OBJECTTYPEN_SERVICE naar de Objecttypen-service.
oc.objecttypes_api_client_config = Service.objects.get(
    slug=os.environ.get("OIP_OBJECTTYPEN_SERVICE", "objecten-api"))
oc.save()
print("Objecten API voor externe taken klaar")

# ------------------------------------------------- actor voor Mijn vragen
ok = Service.objects.get(slug="klantinteracties-api")
basis = ok.api_root.rstrip("/")
headers = {"Authorization": f"Token {os.environ['OPENKLANT_OPENINWONER_TOKEN']}"}
NAAM_ACTOR = "Klantcontactcentrum Voorbeeldstad"
r = requests.get(f"{basis}/actoren", params={"naam": NAAM_ACTOR}, headers=headers, timeout=30)
r.raise_for_status()
actoren = [a for a in r.json()["results"] if a["naam"] == NAAM_ACTOR]
if actoren:
    actor = actoren[0]
else:
    r = requests.post(f"{basis}/actoren", headers=headers, timeout=30, json={
        "naam": NAAM_ACTOR, "soortActor": "organisatorische_eenheid", "indicatieActief": True,
        "actoridentificator": {"objectId": "KCC", "codeObjecttype": "oe", "codeRegister": "demogemeente",
                               "codeSoortObjectId": "code"},
        "actorIdentificatie": {"omschrijving": "Klantcontactcentrum", "emailadres": "kcc@voorbeeldstad.example",
                               "faxnummer": "", "telefoonnummer": ""},
    })
    if r.status_code >= 400:
        raise SystemExit(f"actor aanmaken in Open Klant mislukt: {r.status_code} {r.text[:500]}")
    actor = r.json()
ok2 = OpenKlant2Config.get_solo()
ok2.mijn_vragen_actor = actor["uuid"]
ok2.save()
print(f"actor voor Mijn vragen: {actor['uuid']}")

# ---------------------------------------------------------------- CMS-pagina's
def voeg_plugin_toe(page, slot, plugin_type, **velden):
    content = PageContent._original_manager.get(page=page, language="nl")
    placeholder = Placeholder.objects.get_for_obj(content).get(slot=slot)
    api.add_plugin(placeholder, plugin_type, "nl", **velden)


home = Page.objects.filter(reverse_id="home").first()
if home is None:
    with transaction.atomic():
        home = api.create_page("Home", "cms/fullwidth.html", "nl", in_navigation=True, reverse_id="home")
        home.set_as_homepage()
    voeg_plugin_toe(home, "content", "CMSZakenPlugin", title="Mijn zaken", num_zaken=4)
    voeg_plugin_toe(home, "content", "TasksPlugin", title="Mijn taken",
                    object_type_generieke_dienstverlening=OBJECTTYPE_EXTERNE_TAAK)
    publish_page(home, "nl")
    print("homepage aangemaakt met Mijn zaken en Mijn taken")
else:
    TasksConfig.objects.filter(object_type_generieke_dienstverlening__in=["", None]).update(
        object_type_generieke_dienstverlening=OBJECTTYPE_EXTERNE_TAAK)

PAGINAS = [
    (CasesApphook, "Mijn aanvragen", {"requires_auth": True, "requires_auth_bsn_or_kvk": True,
                                      "menu_icon": "inventory_2"}),
    (ProfileApphook, "Mijn profiel", {"requires_auth": True, "requires_auth_bsn_or_kvk": True,
                                      "menu_icon": "person"}),
    (OpenklantApphook, "Mijn vragen", {"requires_auth": True, "requires_auth_bsn_or_kvk": True,
                                       "menu_icon": "help_outline"}),
    (ProductsApphook, "Onderwerpen", {"menu_icon": "description"}),
]
for hook, titel, extensie in PAGINAS:
    if Page.objects.filter(application_namespace=hook.app_name).exists():
        continue
    create_apphook_page(hook, title=titel, extension_args=dict(extensie), parent_page=home)
    print(f"pagina aangemaakt: {titel}")
print("CMS-pagina's klaar")
