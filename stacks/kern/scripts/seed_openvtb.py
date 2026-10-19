"""Open VTB: API-account voor de demo, een berichttype en voor testinwoner Suzanne (BSN 999993653) een bericht,
een URL-taak en een betaaltaak. Draait in de Django-shell van Open VTB (ORM voor account en berichttype, de
rest via de eigen API op localhost). Idempotent.
    docker compose exec -T -e VTB_TOKEN_DEMO -e BASE_DOMAIN openvtb python src/manage.py shell < scripts/seed_openvtb.py"""
import datetime, os, sys
import requests
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from openvtb.components.berichten.models import BerichtType

D = os.environ["BASE_DOMAIN"]; BSN = "999993653"; RSIN = "002220647"
user, _ = get_user_model().objects.get_or_create(username="demostack-api")
Token.objects.filter(user=user).exclude(key=os.environ["VTB_TOKEN_DEMO"]).delete()
Token.objects.get_or_create(user=user, key=os.environ["VTB_TOKEN_DEMO"])
bt, _ = BerichtType.objects.get_or_create(
    verantwoordelijke_organisatie=f"urn:nld:rsin:{RSIN}", handelings_perspectief="informatie_krijgen",
    defaults={"mijn_overheid_berichtenbox": True})

API = "http://localhost:8000"
H = {"Authorization": f"Token {os.environ['VTB_TOKEN_DEMO']}", "Host": "localhost"}
ONTVANGER = f"urn:nld:brp:bsn:{BSN}"
termijn = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()

def bestaat(pad, **params):
    r = requests.get(f"{API}{pad}", headers=H, params=params, timeout=30); r.raise_for_status()
    return r.json()["count"] > 0

def maak(pad, data):
    r = requests.post(f"{API}{pad}", headers=H, json=data, timeout=30)
    if r.status_code >= 400: print(pad, r.status_code, r.text[:600]); sys.exit(1)
    print("aangemaakt:", data.get("onderwerp") or data.get("titel"))

if not bestaat("/berichten/api/v1/berichten", ontvanger=ONTVANGER):
    maak("/berichten/api/v1/berichten", {
        "onderwerp": "Uw melding is in behandeling",
        "berichtTekst": f"Beste mevrouw Moulin, we hebben uw melding over de losliggende stoeptegel ontvangen. "
                        f"U kunt de voortgang volgen op https://inwoner.{D}/.",
        "ontvanger": ONTVANGER, "berichtType": f"{API}/berichten/api/v1/berichttypen/{bt.uuid}"})
if not bestaat("/taken/api/v1/externetaken", isToegewezenAan=ONTVANGER):
    maak("/taken/api/v1/urltaken", {
        "titel": "Stuur een foto van de losliggende stoeptegel", "status": "open", "handelingsPerspectief": "informatie_geven",
        "einddatumHandelingsTermijn": termijn, "isToegewezenAan": ONTVANGER,
        "details": {"uitvraagLink": f"https://formulieren.{D}/"}})
    maak("/taken/api/v1/betaaltaken", {
        "titel": "Betaal de leges voor uw parkeervergunning", "status": "open", "handelingsPerspectief": "betalen",
        "einddatumHandelingsTermijn": termijn, "isToegewezenAan": ONTVANGER,
        "details": {"bedrag": "52.50", "valuta": "EUR", "transactieomschrijving": "Leges parkeervergunning",
                    "doelrekening": {"naam": "Demogemeente", "iban": "NL02ABNA0123456789"}}})
