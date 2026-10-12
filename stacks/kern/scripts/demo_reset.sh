#!/usr/bin/env bash
# Zet de demodata terug naar een vaste basis, zodat testmeldingen, chats en wijzigingen van bezoekers verdwijnen.
#   ./scripts/demo_reset.sh basis     legt de huidige, schone stand vast (na setup.sh en eventueel handmatig opruimen)
#   ./scripts/demo_reset.sh herstel   zet die stand terug (via cron, elke nacht)
# Teruggezet worden de databases met zaak-, klant- en procesgegevens. Keycloak (accounts) en de inrichting
# van PABC blijven staan. ZaakChat begint leeg en leest de zaken opnieuw in; Mailpit wordt geleegd.
# De dumps bevatten de configuratie van de componenten (ook sleutels) en staan daarom alleen leesbaar voor root.
set -euo pipefail
cd "$(dirname "$0")/.."
DIR=${DEMO_BASIS:-/var/lib/demostack/basis}
DBS="openzaak openklant objects objecttypes openforms opennotificaties kiss zac gzac openinwoner"
# Diensten die deze databases gebruiken (alleen de draaiende worden gestopt en weer gestart)
APPS="openzaak openzaak-celery openzaak-beat openklant openklant-celery objects objects-celery objecttypes
  openforms openforms-celery openforms-beat opennotificaties opennotificaties-celery opennotificaties-beat
  kiss zac gzac-backend gzac openinwoner openinwoner-celery openinwoner-beat zaakchat zaakchat-koppeling"

case "${1:-}" in
  basis)
    install -d -m 700 "$DIR"
    for db in $DBS; do
      docker compose exec -T db pg_dump -U postgres -Fc "$db" > "$DIR/$db.dump.tmp" && mv "$DIR/$db.dump.tmp" "$DIR/$db.dump"
    done
    chmod 600 "$DIR"/*.dump; date -Iseconds > "$DIR/gemaakt"
    echo "Basis vastgelegd in $DIR"
    ;;
  herstel)
    [ -f "$DIR/gemaakt" ] || { echo "Geen basis in $DIR; eerst: $0 basis"; exit 1; }
    for db in $DBS; do [ -s "$DIR/$db.dump" ] || { echo "Dump van $db ontbreekt of is leeg; niets veranderd"; exit 1; }; done
    draaiend=$(docker compose ps --services --status running)
    stop=$(for s in $APPS; do echo "$draaiend" | grep -qx "$s" && echo "$s"; done | tr '\n' ' ')
    docker compose stop $stop >/dev/null 2>&1 || true
    for db in $DBS; do
      docker compose exec -T db psql -U postgres -qc "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$db' AND pid <> pg_backend_pid();" >/dev/null
      docker compose exec -T db dropdb -U postgres --if-exists "$db"
      docker compose exec -T db createdb -U postgres -O "$db" "$db"
      # Als postgres terugzetten: eigenaars, schema's en extensies (PostGIS) komen mee uit de dump
      docker compose exec -T db pg_restore -U postgres -d "$db" < "$DIR/$db.dump" 2>&1 | head -5 || true
    done
    # ZaakChat begint leeg; de koppeling leest de zaken bij het starten opnieuw in
    docker compose rm -f zaakchat >/dev/null 2>&1 || true
    docker volume rm -f kern_zaakchat-data >/dev/null 2>&1 || true
    docker compose restart mailpit >/dev/null 2>&1 || true
    docker compose up -d $stop >/dev/null 2>&1
    # Zoekindexen bijwerken zodra de werkplekken weer draaien
    set -a; . ./.env; set +a
    for _ in $(seq 1 60); do curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8111/ | grep -qE '200|302' && break; sleep 5; done
    curl -s -o /dev/null -H "X-API-KEY: $ZAC_INTERNAL_KEY" http://127.0.0.1:8111/rest/internal/indexeren/herindexeren/ZAAK || true
    docker compose run --rm -T kiss-sync-vac >/dev/null 2>&1 || true
    echo "Demodata teruggezet naar de basis van $(cat "$DIR/gemaakt")"
    ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
