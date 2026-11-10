import os
from django.core.management import call_command
from zgw_consumers.models import Service
from open_inwoner.openzaak.models import ZGWApiGroupConfig
for g in ZGWApiGroupConfig.objects.all():
    g.klant_backend = "openklant2"; g.save()

from cms.models import Page, PageContent, Placeholder
from open_inwoner.cms.tests import cms_tools as t
from open_inwoner.cms.profile.cms_apps import ProfileApphook
from open_inwoner.cms.cases.cms_apps import CasesApphook
if not Page.objects.exists():
    home = t.create_homepage()
    t.create_apphook_page(ProfileApphook, title="Mijn profiel", extension_args={"requires_auth": True})
    t.create_apphook_page(CasesApphook, title="Mijn aanvragen", extension_args={"requires_auth": True, "requires_auth_bsn_or_kvk": True})
    t.publish_page(home, "nl")
    print("cms-pagina's aangemaakt")

from open_inwoner.configurations.models import SiteConfiguration
sc = SiteConfiguration.get_solo(); sc.name = "Demogemeente"
if hasattr(sc, "login_allow_registration"): sc.login_allow_registration = False
sc.save()

call_command("zgw_import_data")

from open_inwoner.gesprekken.models import MijnGesprekkenConfig
c = MijnGesprekkenConfig.get_solo()
c.enabled = True; c.service = Service.objects.get(slug="gesprekken")
c.organisatie_naam = "Demogemeente"; c.burger_mag_gesprek_starten = True
c.ontvanger_actor_url = os.environ["ONTVANGER_ACTOR"]; c.ontvanger_actor_naam = "Team Openbare Ruimte"
c.bijlagen_ingeschakeld = True; c.polling_interval_seconden = 3
c.save()

from open_inwoner.accounts.models import User
from open_inwoner.accounts.choices import LoginTypeChoices
u = User.objects.filter(bsn="999993653").first()
if not u:
    u = User.objects.create(email="suzanne.moulin@demogemeente.local", bsn="999993653", login_type=LoginTypeChoices.digid,
                            first_name="Suzanne", last_name="Moulin", is_prepopulated=True)
    u.set_unusable_password(); u.save()
if not User.objects.filter(email="admin@demogemeente.local").exists():
    User.objects.create_superuser("admin@demogemeente.local", os.environ["DJANGO_SUPERUSER_PASSWORD"])
print("open inwoner inrichting ok")

# Zaaktitel uit zaak.omschrijving (bijvoorbeeld "Losliggende stoeptegel: Dorpsstraat 12") in plaats van het zaaktype
from open_inwoner.openzaak.models import OpenZaakConfig
oz = OpenZaakConfig.get_solo(); oz.derive_zaak_titel_from = "zaak_omschrijving"; oz.save()
