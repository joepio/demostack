#!/bin/sh
# Zet OpenEvents terug op leeg en laat de simulator opnieuw historie schrijven.
# De zaakspiegel vult zich weer vanuit nieuwe notificaties van Open Zaak.
set -e
cd "$(dirname "$0")"
docker compose down oe-server oe-sim
docker volume rm oedemo_data >/dev/null
docker compose up -d
echo "OpenEvents leeggemaakt"
