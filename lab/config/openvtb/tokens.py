"""Maakt de API-gebruikers en -tokens van Open VTB aan (idempotent).

Open VTB 0.2.0 heeft geen setup-configuration-stap voor tokens; de API gebruikt DRF
TokenAuthentication (Authorization: Token <key>). Dit script draait na
setup_configuration in de init-container: `python src/manage.py shell < tokens.py`.
De tokens staan in .env (OPENVTB_BEHEER_TOKEN, OPENVTB_PORTAAL_TOKEN).
"""
import os

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

beheerder, _ = User.objects.get_or_create(username=os.environ.get("ADMIN_USERNAME", "admin"))
beheerder.is_staff = beheerder.is_superuser = True
beheerder.email = "admin@voorbeeldstad.example"
beheerder.set_password(os.environ["ADMIN_PASSWORD"])
beheerder.save()

for gebruikersnaam, var in (("demogemeente-beheer", "OPENVTB_BEHEER_TOKEN"), ("burgerportaal", "OPENVTB_PORTAAL_TOKEN")):
    user, _ = User.objects.get_or_create(username=gebruikersnaam)
    user.set_unusable_password()
    user.save()
    sleutel = os.environ[var]
    Token.objects.filter(user=user).exclude(key=sleutel).delete()
    Token.objects.get_or_create(user=user, key=sleutel)
    print(f"token voor {gebruikersnaam} klaar")
