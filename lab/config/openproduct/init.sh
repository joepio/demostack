#!/bin/bash
# Init-container van Open Product: migraties en setup-configuration, daarna de
# Uniforme Productnamenlijst (UPL) uit een lokale kopie laden en een API-token
# voor de beheerder aanmaken. Idempotent.
set -euo pipefail

/setup_configuration.sh

# load_upl werkt bestaande namen bij, dus opnieuw draaien kan geen kwaad
python src/manage.py load_upl --file /app/init/UPL-actueel.csv

python src/manage.py shell -c "
import os
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()
user, _ = User.objects.get_or_create(username='demogemeente-beheer', defaults={'is_staff': True, 'is_superuser': True, 'email': 'beheer@voorbeeldstad.example'})
user.is_superuser = True
user.is_staff = True
user.save()
key = os.environ['OPENPRODUCT_BEHEER_TOKEN']
Token.objects.filter(user=user).exclude(key=key).delete()
Token.objects.get_or_create(user=user, key=key)
print('API-token voor demogemeente-beheer staat klaar')
"
