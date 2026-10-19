#!/usr/bin/env bash
# Kies en bedien een stack van de demogemeente.
#
#   scripts/stack.sh list                      alle stacks met status
#   scripts/stack.sh up <naam> [--plugin <map>]... [--geen-seed]
#                                              starten, wachten tot gezond, testdata laden;
#                                              --plugin (of PLUGINS="<map> <map>") voegt
#                                              een component van een leverancier toe
#   scripts/stack.sh seed <naam>               testdata laden (idempotent)
#   scripts/stack.sh test <naam> [--alleen gezondheid,rook,zgw,burger-isolatie,mijn-apis]
#                                              gedeelde testsuite, uitvoer in results/<naam>.json en .md
#   scripts/stack.sh down <naam> [--behoud-data]
#                                              stoppen en (standaard) volumes wissen
#   scripts/stack.sh pull <naam>               images ophalen (met uitwijk naar mirror.gcr.io)
#   scripts/stack.sh ps|logs <naam> [...]      docker compose ps / logs
#   scripts/stack.sh compose <naam> <args...>  willekeurig docker compose-commando
#   scripts/stack.sh opruimen                  ongebruikte images en build-cache weg
#
# Er draait steeds één stack tegelijk: alle stacks gebruiken dezelfde hostpoorten.
source "$(dirname "$0")/lib/common.sh"

gebruik() { sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit "${1:-2}"; }

cmd_list() {
    local s
    printf '%-8s %-10s %s\n' STACK STATUS TITEL
    for s in $(alle_stacks); do
        (laad_stack "$s"; printf '%-8s %-10s %s\n' "$s" "$STACK_STATUS" "$STACK_TITEL")
    done
    local f
    for f in "$STATE_DIR"/*.plugins; do
        [ -f "$f" ] || continue
        echo
        echo "Plug-ins van stack $(basename "$f" .plugins): $(tr '\n' ' ' < "$f")"
    done
    local actief
    actief="$(draaiende_stacks | tr '\n' ' ')"
    [ -n "$actief" ] && echo && echo "Containers aanwezig van: $actief"
    return 0
}

cmd_up() {
    local andere seed=1 plugins=() d
    while [ $# -gt 0 ]; do
        case "$1" in
            --geen-seed) seed=0; shift ;;
            --plugin) plugins+=("${2:?--plugin vraagt een map}"); shift 2 ;;
            --plugin=*) plugins+=("${1#--plugin=}"); shift ;;
            *) fout "onbekende optie $1"; exit 2 ;;
        esac
    done
    if [ ${#plugins[@]} -eq 0 ] && [ -n "${PLUGINS:-}" ]; then
        read -r -a plugins <<< "$PLUGINS"
    fi
    laad_plugins_expliciet "${plugins[@]}"
    andere="$(draaiende_stacks | grep -vx "$PROJECT" | tr '\n' ' ' || true)"
    if [ -n "$andere" ]; then
        fout "er staan nog containers van een andere stack: $andere"
        echo "Stop die eerst met: scripts/stack.sh down <naam>" >&2
        exit 1
    fi
    zorg_voor_env
    info "stack: $STACK ($STACK_TITEL)"
    [ ${#PLUGIN_DIRS[@]} -gt 0 ] && info "plug-ins: $(plugin_namen)"
    # Componenten zonder bereikbaar image bouwt de stack zelf (alleen wat nog ontbreekt)
    if [ -x "$STACK_DIR/bouw.sh" ]; then
        info "images bouwen die de stack zelf maakt (stacks/$STACK/bouw.sh)"
        "$STACK_DIR/bouw.sh"
    fi
    for d in "${PLUGIN_DIRS[@]}"; do
        if [ -x "$d/bouw.sh" ]; then
            info "images bouwen voor plug-in $(plugin_naam "$d") ($d/bouw.sh)"
            DEMO_STACK="$STACK" PLUGIN_DIR="$d" "$d/bouw.sh"
        fi
    done
    bewaar_plugins
    cmd_pull --alleen-ontbrekend
    compose up -d --remove-orphans
    wacht_op_gezond 1200
    if [ "$seed" = 1 ]; then
        cmd_seed
    fi
    info "klaar. Test met: scripts/stack.sh test $STACK"
}

cmd_seed() {
    info "gedeelde testdata laden (seed/seed.py)"
    compose run --rm --no-deps tools seed/seed.py
    if [ -f "$STACK_DIR/seed.py" ]; then
        info "stack-specifieke testdata (stacks/$STACK/seed.py)"
        compose run --rm --no-deps tools "stacks/$STACK/seed.py"
    fi
    # Stappen die in een draaiende container moeten (bijv. een synchronisatie die anders
    # pas 's nachts loopt); het script mag de functie compose gebruiken
    if [ -f "$STACK_DIR/na-seed.sh" ]; then
        info "stappen na de seed (stacks/$STACK/na-seed.sh)"
        # shellcheck source=/dev/null
        . "$STACK_DIR/na-seed.sh"
    fi
    local d
    for d in "${PLUGIN_DIRS[@]}"; do
        if [ -f "$d/seed.py" ]; then
            info "testdata voor plug-in $(plugin_naam "$d")"
            compose run --rm --no-deps tools "/plugins/$(plugin_naam "$d")/seed.py"
        fi
    done
}

zorg_voor_respect() {
    local dir="$ROOT/tests/respect"
    [ -x "$dir/node_modules/.bin/redocly" ] && return 0
    info "Redocly CLI installeren in tests/respect (eenmalig)"
    if command -v npm >/dev/null; then
        (cd "$dir" && npm ci --no-audit --no-fund --loglevel=error)
    else
        docker run --rm -v "$dir:/w" -w /w node:22.22.0-alpine npm ci --no-audit --no-fund --loglevel=error
    fi
}

# Rapportnaam: de stack, met plug-ins <stack>+<plug-in>[+<plug-in>]
rapport_naam() {
    local n="$STACK" p
    for p in $(plugin_namen); do n="$n+$p"; done
    printf '%s' "$n"
}

cmd_test() {
    local alleen="" status=0 naam raw
    naam="$(rapport_naam)"
    raw="$ROOT/results/raw/$naam"
    while [ $# -gt 0 ]; do
        case "$1" in
            --alleen) alleen="$2"; shift 2 ;;
            *) fout "onbekende optie $1"; exit 2 ;;
        esac
    done
    mkdir -p "$raw"
    rm -f "$raw"/*.json
    compose ps -a --format json > "$raw/ps.json"
    [ ${#PLUGIN_DIRS[@]} -gt 0 ] && info "plug-ins: $(plugin_namen); rapport results/$naam.md"
    info "testsuite, deel 1: Python-controles en plan voor de aansluitprofielen"
    compose run --rm --no-deps tools tests/run.py --stack "$STACK" --rapport "$naam" ${alleen:+--alleen "$alleen"} || status=$?
    if [ "$status" -ne 0 ]; then
        fout "tests/run.py stopte met code $status"
        exit "$status"
    fi
    if [ -s "$raw/respect-jobs.json" ] && [ "$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$raw/respect-jobs.json")" != 0 ]; then
        zorg_voor_respect
        info "testsuite, deel 2: aansluitprofielen (Arazzo, Redocly Respect)"
        compose run --rm --no-deps respect tests/respect/run.mjs "results/raw/$naam/respect-jobs.json"
    fi
    info "testsuite, deel 3: rapport"
    compose run --rm --no-deps tools tests/rapport.py --stack "$STACK" --rapport "$naam"
}

cmd_down() {
    if [ "${1:-}" = "--behoud-data" ]; then
        compose --profile tools down --remove-orphans
    else
        compose --profile tools down --volumes --remove-orphans
    fi
    rm -f "$STATE_DIR/$STACK.plugins" "$STATE_DIR/$STACK.plugins.yml"
}

# Haalt de images van de stack op. Bij een fout (bijvoorbeeld 429 van Docker Hub) wordt
# hetzelfde image via mirror.gcr.io geprobeerd en lokaal onder de originele naam getagd.
cmd_pull() {
    local img alleen_ontbrekend="${1:-}" pad
    # Images van services met build: (stacks en plug-ins die zelf bouwen) niet ophalen
    for img in $(compose --profile tools config --format json | python3 -c '
import json, sys
diensten = json.load(sys.stdin).get("services", {}).values()
print("\n".join(sorted({d["image"] for d in diensten if d.get("image") and "build" not in d})))'); do
        if [ "$alleen_ontbrekend" = "--alleen-ontbrekend" ] && docker image inspect "$img" >/dev/null 2>&1; then
            continue
        fi
        # Lokaal gebouwde images (stacks/<naam>/bouw.sh) niet ophalen
        case "$img" in demogemeente/*) continue ;; esac
        if docker pull -q "$img" >/dev/null 2>&1; then
            echo "opgehaald: $img"
            continue
        fi
        case "$img" in
            */*/*) pad="" ;;                       # ander register dan Docker Hub
            */*) pad="$img" ;;
            *) pad="library/$img" ;;
        esac
        if [ -n "$pad" ] && docker pull -q "mirror.gcr.io/$pad" >/dev/null 2>&1; then
            docker tag "mirror.gcr.io/$pad" "$img"
            docker rmi "mirror.gcr.io/$pad" >/dev/null
            echo "opgehaald via mirror.gcr.io: $img"
        else
            waarschuw "kon $img niet ophalen"
        fi
    done
}

cmd_opruimen() {
    docker image prune -f
    docker builder prune -f
    docker system df
}

[ $# -ge 1 ] || gebruik
actie="$1"; shift
case "$actie" in
    list|ls) cmd_list ;;
    opruimen|prune) cmd_opruimen ;;
    up|seed|test|down|pull|ps|logs|compose)
        laad_stack "${1:-}"; shift
        # up kiest zijn plug-ins zelf; de rest gebruikt die waarmee de stack gestart is
        [ "$actie" = up ] || laad_plugins
        case "$actie" in
            up) cmd_up "$@" ;;
            seed) cmd_seed ;;
            test) cmd_test "$@" ;;
            down) cmd_down "$@" ;;
            pull) cmd_pull "$@" ;;
            ps) compose ps "$@" ;;
            logs) compose logs "$@" ;;
            compose) compose "$@" ;;
        esac ;;
    -h|--help|help) gebruik 0 ;;
    *) fout "onbekende actie '$actie'"; gebruik ;;
esac
