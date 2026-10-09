"""Maakt of herstelt de beheerder (superuser) van een Django-component, idempotent.

Voor componenten zonder eigen superuser-variabelen (Open Archiefbeheer, Open Beheer).
Gebruik in een init-container: python src/manage.py shell < /tools/beheerder.py
"""
import os

from django.contrib.auth import get_user_model

User = get_user_model()
naam = os.environ.get("ADMIN_USERNAME", "admin")
velden = {User.USERNAME_FIELD: naam} if User.USERNAME_FIELD != "email" else {"email": "admin@voorbeeldstad.example"}
gebruiker = User.objects.filter(**velden).first() or User(**velden)
if hasattr(gebruiker, "email") and not gebruiker.email:
    gebruiker.email = "admin@voorbeeldstad.example"
gebruiker.is_staff = gebruiker.is_superuser = gebruiker.is_active = True
gebruiker.set_password(os.environ["ADMIN_PASSWORD"])
gebruiker.save()
print(f"beheerder klaar: {naam}")
