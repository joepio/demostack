# Draait via: manage.py shell < scripts/openforms_inrichting.py  (env: BASE_DOMAIN, DIGID_OIDC_SECRET). DigiD (demo) via Keycloak en privacytekst.
import os
from mozilla_django_oidc_db.models import OIDCClient, OIDCProvider
D = os.environ["BASE_DOMAIN"]
base = f"https://keycloak.{D}/realms/demogemeente/protocol/openid-connect"
prov, _ = OIDCProvider.objects.get_or_create(identifier="keycloak-digid")
prov.oidc_op_authorization_endpoint = f"{base}/auth"; prov.oidc_op_token_endpoint = f"{base}/token"
prov.oidc_op_user_endpoint = f"{base}/userinfo"; prov.oidc_op_jwks_endpoint = f"{base}/certs"
prov.oidc_op_logout_endpoint = f"{base}/logout"; prov.oidc_use_nonce = True
prov.save()
c = OIDCClient.objects.get(identifier="oidc-digid")
c.enabled = True; c.oidc_provider = prov
c.oidc_rp_client_id = "digid"; c.oidc_rp_client_secret = os.environ["DIGID_OIDC_SECRET"]
c.oidc_rp_scopes_list = ["openid"]; c.oidc_rp_sign_algo = "RS256"
c.options = {"identity_settings": {"bsn_claim_path": ["bsn"]},
             "loa_settings": {"claim_path": [], "default": "urn:oasis:names:tc:SAML:2.0:ac:classes:MobileTwoFactorContract",
                              "value_mapping": []}}
c.save()
print("openforms digid ok")

# Privacytekst in het Nederlands, met link naar de welkomstpagina
from openforms.config.models import GlobalConfiguration
g = GlobalConfiguration.get_solo()
g.privacy_policy_label_nl = "Ja, ik heb de {% privacy_policy %} gelezen en ga akkoord met de verwerking van mijn gegevens."
g.privacy_policy_url = f"https://{D}/"
# Kaart start in het centrum van de 'demostad' (Amersfoort), waar ook de demomeldingen liggen
g.form_map_default_latitude = 52.1561
g.form_map_default_longitude = 5.3878
g.form_map_default_zoom_level = 15
g.save()
print("openforms privacy ok")
