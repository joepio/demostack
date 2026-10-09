"""Aanvullende configuratie van Open Formulieren (stack maykin), idempotent.

Wat setup-configuration van Open Formulieren 4.0 nog niet kan:
- beheerder en API-token voor de seed (formulieren aanmaken via de API);
- BRP-prefill: Haal Centraal BRP Personen 2.0 op de BRP-mock;
- catalogus (domein en RSIN) van de ZGW-groep, zodat formulieren het zaaktype op
  identificatie vinden.
Draait in de init-container: `python src/manage.py shell < configureer.py`.
"""
import os

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from zgw_consumers.models import Service

from openforms.config.models import GlobalConfiguration
from openforms.contrib.haal_centraal.models import HaalCentraalConfig
from openforms.registrations.contrib.zgw_apis.models import ZGWApiGroupConfig

User = get_user_model()
beheerder, _ = User.objects.get_or_create(username=os.environ.get("ADMIN_USERNAME", "admin"))
beheerder.is_staff = beheerder.is_superuser = True
beheerder.email = "admin@voorbeeldstad.example"
beheerder.set_password(os.environ["ADMIN_PASSWORD"])
beheerder.save()
sleutel = os.environ["OPENFORMULIEREN_BEHEER_TOKEN"]
Token.objects.filter(user=beheerder).exclude(key=sleutel).delete()
Token.objects.get_or_create(user=beheerder, key=sleutel)
print("beheerder en API-token klaar")

hc = HaalCentraalConfig.get_solo()
hc.brp_personen_service = Service.objects.get(slug="brp-personen")
hc.brp_personen_version = "2.0"
hc.save()
print("BRP-prefill: Haal Centraal BRP Personen 2.0 (BRP-mock)")

groep = ZGWApiGroupConfig.objects.get(identifier="open-zaak-voorbeeldstad")
groep.catalogue_domain = "VBSTD"
groep.catalogue_rsin = os.environ.get("GEMEENTE_RSIN", "999990007")
groep.save()
print("ZGW-groep: catalogus VBSTD")

gc = GlobalConfiguration.get_solo()
gc.main_website = os.environ.get("OPENINWONER_PUBLIEK", "http://localhost:8103/")
gc.organization_name = os.environ.get("GEMEENTE_NAAM", "Gemeente Voorbeeldstad")
# Virusscan van uploads met ClamAV (PodiumD draait ClamAV naast Open Formulieren)
if os.environ.get("CLAMAV_HOST"):
    gc.enable_virus_scan = True
    gc.clamav_host = os.environ["CLAMAV_HOST"]
    gc.clamav_port = int(os.environ.get("CLAMAV_PORT", "3310"))
    gc.clamav_timeout = int(os.environ.get("CLAMAV_TIMEOUT", "30"))
gc.save()
print("algemene configuratie klaar")
