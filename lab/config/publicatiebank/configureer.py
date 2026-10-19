"""Inrichting van de GPP-publicatiebank 2.1.0 (stack vcg), idempotent.

De publicatiebank heeft geen setup-configuration; deze inrichting draait in de
init-container met `python src/manage.py shell < /config/configureer.py`, na de
migraties en het laden van de waardelijsten (informatiecategorieen, organisaties,
thema's) door het image zelf.

1. Service "Documenten API" naar Open Zaak (ZGW-JWT, client gpp-publicatiebank). De
   publicatiebank bewaart de documenten van publicaties daar.
2. Algemene configuratie: die service en het RSIN van Gemeente Voorbeeldstad.
3. API-applicaties (Authorization: Token ...):
   - demogemeente-beheer   lezen en schrijven (seed, tests)
   - gpp-zoeken            alleen lezen: zoals het publieke zoekportaal de publicaties
                           ophaalt (GPP-zoeken en het burgerportaal draaien hier niet)
"""
import os

from woo_publications.api.models import Application
from woo_publications.config.models import GlobalConfiguration
from zgw_consumers.constants import APITypes, AuthTypes
from zgw_consumers.models import Service

service, _ = Service.objects.update_or_create(
    slug="documenten-api-open-zaak",
    defaults={
        "label": "Open Zaak - Documenten API",
        "api_type": APITypes.drc,
        "api_root": "http://openzaak.local:8000/documenten/api/v1/",
        "api_connection_check_path": "enkelvoudiginformatieobjecten",
        "auth_type": AuthTypes.zgw,
        "client_id": "gpp-publicatiebank",
        "secret": os.environ["ZGW_PUBLICATIEBANK_SECRET"],
        "user_id": "gpp-publicatiebank",
        "user_representation": "GPP-publicatiebank",
    },
)

config = GlobalConfiguration.get_solo()
config.documents_api_service = service
config.organisation_rsin = os.environ.get("GEMEENTE_RSIN", "999990007")
config.gpp_app_publication_url_template = (
    f"http://localhost:{os.environ.get('PORT_PUBLICATIEBANK', '8252')}/admin/publications/publication/<UUID>/change/"
)
config.save()

for label, var, rechten in (
    ("demogemeente-beheer", "PUBLICATIEBANK_BEHEER_TOKEN", ["read", "write"]),
    ("gpp-zoeken", "PUBLICATIEBANK_PUBLIEK_TOKEN", ["read"]),
):
    app = Application.objects.filter(contact_person=label).first() or Application(contact_person=label)
    app.token = os.environ[var]
    app.permissions = rechten
    app.email = f"{label}@voorbeeldstad.example"
    app.save()
    print(f"API-applicatie klaar: {label} ({', '.join(rechten)})")

print("publicatiebank ingericht: Documenten API van Open Zaak, RSIN", config.organisation_rsin)
