"""Maakt de API-gebruikers en -tokens van OpenPlan aan (idempotent).

OpenPlan 0.1.0 heeft geen setup-configuration; de API gebruikt DRF
TokenAuthentication (Authorization: Token <key>). Dit script draait na de migraties
in de init-container: `python src/manage.py shell < tokens.py`.
Het token staat in .env (OPENPLAN_BEHEER_TOKEN). De API kent geen leesrechten
apart: elk geldig token mag lezen en schrijven.
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

for gebruikersnaam, var in (("demogemeente-beheer", "OPENPLAN_BEHEER_TOKEN"),):
    user, _ = User.objects.get_or_create(username=gebruikersnaam)
    user.set_unusable_password()
    user.save()
    sleutel = os.environ[var]
    Token.objects.filter(user=user).exclude(key=sleutel).delete()
    Token.objects.get_or_create(user=user, key=sleutel)
    print(f"token voor {gebruikersnaam} klaar")
