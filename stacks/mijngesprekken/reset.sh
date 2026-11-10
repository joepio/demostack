#!/bin/sh
# Zet de demo terug op leeg: geen gesprekken, geen klantcontacten. Inrichting, actoren en Suzanne blijven.
set -e
cd "$(dirname "$0")"
docker compose stop mg-oip-volger >/dev/null
docker compose exec -T mg-db psql -U postgres -d grc_db -qc "TRUNCATE bijlagen, bestanden, gelezengespreksbijdragen, gespreksbijdragen, gespreksdeelnames, gesprekken, events, organisatie_nummers RESTART IDENTITY CASCADE"
docker compose exec -T mg-db psql -U postgres -d openinwoner -qc "DELETE FROM gesprekken_verwerktgesprekevent; DELETE FROM gesprekken_gesprekgezien; DELETE FROM gesprekken_gesprekkeneventstroom"
echo "from openklant.components.klantinteracties.models import Klantcontact; Klantcontact.objects.all().delete()" | docker compose exec -T mg-openklant python src/manage.py shell >/dev/null 2>&1
docker run --rm --network mgdemo_default curlimages/curl:8.11.1 -s -o /dev/null -X PUT http://mg-s3:5000/gesprekken || true
docker compose start mg-oip-volger >/dev/null
echo "demo leeggemaakt"
