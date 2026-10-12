"""Open Inwoner: wat setup_configuration niet kan (idempotent). Draait met manage.py shell.
Klantensysteem en BRP koppelen, Objecten voor taken, de CMS-pagina's (Mijn profiel, Mijn aanvragen,
Mijn berichten, takenblok op de homepage), DigiD aan, zaaktypen importeren en het abonnement op
zaaknotificaties registreren bij Open Notificaties."""
import os
from django.core.management import call_command
from zgw_consumers.models import Service
from open_inwoner.openzaak.models import ZGWApiGroupConfig
from open_inwoner.haalcentraal.models import HaalCentraalConfig
from objectsapiclient.models import ObjectsAPIServiceConfiguration
from notifications.models import NotificationsAPIConfig, Subscription

D = os.environ["BASE_DOMAIN"]
for g in ZGWApiGroupConfig.objects.all():
    g.klant_backend = "openklant2"; g.save()

hc = HaalCentraalConfig.get_solo(); hc.service = Service.objects.get(slug="brp"); hc.brp_version = "2.0"; hc.save()

oc = ObjectsAPIServiceConfiguration.get_solo()
oc.objects_api_client_config = Service.objects.get(slug="objecten")
oc.objecttypes_api_client_config = Service.objects.get(slug="objecttypen"); oc.save()

# Pagina's: dezelfde helpers die Open Inwoner in de eigen tests gebruikt
from cms.models import Page
from cms.api import add_plugin
from cms.models import PageContent, Placeholder
from open_inwoner.cms.tests import cms_tools as t
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
from open_inwoner.cms.inbox.cms_apps import InboxApphook
if not Page.objects.exists():
    home = t.create_homepage()
    t.create_apphook_page(ProfileApphook, title="Mijn profiel", extension_args={"requires_auth": True})
    t.create_apphook_page(CasesApphook, title="Mijn aanvragen", extension_args={"requires_auth": True, "requires_auth_bsn_or_kvk": True})
    t.create_apphook_page(InboxApphook, title="Mijn berichten", extension_args={"requires_auth": True})
    pc = PageContent._original_manager.get(page=home, language="nl")
    ph = Placeholder.objects.get_for_obj(pc).get(slot="content")
    add_plugin(placeholder=ph, plugin_type="TasksPlugin", language="nl", title="Mijn taken",
               object_type_generieke_dienstverlening=os.environ["TAAK_OT"])
    t.publish_page(home, "nl")
    print("cms-pagina's aangemaakt")

from open_inwoner.configurations.models import SiteConfiguration
sc = SiteConfiguration.get_solo()
sc.name = "Demogemeente"
for f in ("login_allow_registration",):
    if hasattr(sc, f): setattr(sc, f, False)
sc.save()

call_command("zgw_import_data")

nc, _ = NotificationsAPIConfig.objects.get_or_create(notifications_api_service=Service.objects.get(slug="notificaties"))
cb = f"https://inwoner.{D}/api/openzaak/notifications/webhook/zaken"
sub = Subscription.objects.filter(callback_url=cb).first()
if not sub:
    sub = Subscription.objects.create(notifications_api_config=nc, callback_url=cb, client_id="oip-nc",
                                      secret=os.environ["OIP_NC_SECRET"][:50], channels=["zaken"])
if not sub._subscription:
    sub.register(); print("abonnement geregistreerd:", sub._subscription)
print("open inwoner inrichting ok")
