#!/usr/bin/env bash
# Gedeelde functies voor scripts/stack.sh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STACKS="$ROOT/stacks"

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
waarschuw() { printf '\033[1;33mLET OP:\033[0m %s\n' "$*" >&2; }
fout() { printf '\033[1;31mFOUT:\033[0m %s\n' "$*" >&2; }

# Alle stacks: mappen onder stacks/ met een stack.env (basis is geen stack).
alle_stacks() {
    local d
    for d in "$STACKS"/*/; do
        [ -f "$d/stack.env" ] && basename "$d"
    done
}

# Laadt stacks/<naam>/stack.env en zet de variabelen die compose en de tests nodig hebben.
laad_stack() {
    STACK="${1:?geef een stacknaam, zie: scripts/stack.sh list}"
    STACK_DIR="$STACKS/$STACK"
    if [ ! -f "$STACK_DIR/stack.env" ]; then
        fout "onbekende stack '$STACK'. Beschikbaar: $(alle_stacks | tr '\n' ' ')"
        exit 2
    fi
    STACK_TITEL="" STACK_STATUS="" STACK_COMPOSE="" DB_EXTRA=""
    # shellcheck disable=SC1090
    set -a; . "$STACK_DIR/stack.env"; set +a
    export DEMO_STACK="$STACK" DB_EXTRA DEMO_UID="$(id -u)" DEMO_GID="$(id -g)"
    PROJECT="demogemeente-$STACK"

    PLUGIN_DIRS=()
}

# ------------------------------------------------------------------ plug-ins
# Een plug-in is een map met plugin.yaml, compose.yml en optioneel stacks/<stack>.yml,
# env.example, bouw.sh en tests.py (contract: docs/PLUGINS.md). De actieve plug-ins van
# een stack staan in .demostack/<stack>.plugins, zodat test, seed en down dezelfde set
# gebruiken als up.
STATE_DIR="$ROOT/.demostack"

plugin_naam() {
    sed -n 's/^naam:[[:space:]]*["'"'"']\{0,1\}\([a-z0-9][a-z0-9-]*\).*/\1/p' "$1/plugin.yaml" | head -n1
}

plugin_var() {   # mijn-portaal -> PLUGIN_MIJN_PORTAAL_DIR
    printf 'PLUGIN_%s_DIR' "$(printf '%s' "$1" | tr 'a-z-' 'A-Z_')"
}

# Controleert een plug-in-map en geeft het absolute pad terug.
plugin_pad() {
    local d="$1" naam stacks
    case "$d" in /*) ;; *) if [ -d "$PWD/$d" ]; then d="$PWD/$d"; else d="$ROOT/$d"; fi ;; esac
    if [ ! -f "$d/plugin.yaml" ] || [ ! -f "$d/compose.yml" ]; then
        fout "geen plug-in in '$1': plugin.yaml en compose.yml zijn verplicht (docs/PLUGINS.md)"
        exit 2
    fi
    d="$(cd "$d" && pwd)"
    naam="$(plugin_naam "$d")"
    if [ -z "$naam" ]; then
        fout "$d/plugin.yaml heeft geen geldige 'naam:' (kleine letters, cijfers en -)"
        exit 2
    fi
    # Optioneel: "stacks: [kern, maykin]" beperkt de plug-in tot die stacks
    stacks="$(sed -n 's/^stacks:[[:space:]]*\[\(.*\)\].*/\1/p' "$d/plugin.yaml" | tr -d ' "'"'"'' | tr ',' ' ')"
    if [ -n "$stacks" ] && ! printf ' %s ' "$stacks" | grep -q " $STACK "; then
        fout "plug-in $naam ondersteunt stack $STACK niet (alleen: $stacks)"
        exit 2
    fi
    printf '%s\n' "$d"
}

# Zet PLUGIN_DIRS (absolute paden) en exporteert PLUGIN_<NAAM>_DIR en DEMOSTACK_PLUGINS.
# laad_plugins: de plug-ins waarmee de stack gestart is (.demostack/<stack>.plugins).
# laad_plugins_expliciet <map>...: precies deze plug-ins (ook geen), voor up.
laad_plugins() {
    local d lijst=()
    if [ -f "$STATE_DIR/$STACK.plugins" ]; then
        while IFS= read -r d; do [ -n "$d" ] && lijst+=("$d"); done < "$STATE_DIR/$STACK.plugins"
    fi
    laad_plugins_expliciet "${lijst[@]}"
}

laad_plugins_expliciet() {
    local d pad naam namen=() binnen=()
    PLUGIN_DIRS=()
    for d in "$@"; do
        pad="$(plugin_pad "$d")" || exit 2
        PLUGIN_DIRS+=("$pad")
    done
    for d in "${PLUGIN_DIRS[@]}"; do
        naam="$(plugin_naam "$d")"
        if printf ' %s ' "${namen[*]:-}" | grep -q " $naam "; then
            fout "plug-in $naam staat er twee keer in"
            exit 2
        fi
        namen+=("$naam")
        binnen+=("/plugins/$naam")
        export "$(plugin_var "$naam")=$d"
    done
    DEMOSTACK_PLUGINS="${binnen[*]:-}"
    export DEMOSTACK_PLUGINS
    schrijf_plugin_compose
}

# Bewaart de plug-ins van de stack voor de volgende commando's.
bewaar_plugins() {
    mkdir -p "$STATE_DIR"
    if [ ${#PLUGIN_DIRS[@]} -eq 0 ]; then
        rm -f "$STATE_DIR/$STACK.plugins"
    else
        printf '%s\n' "${PLUGIN_DIRS[@]}" > "$STATE_DIR/$STACK.plugins"
    fi
}

plugin_namen() {
    local d uit=()
    for d in "${PLUGIN_DIRS[@]}"; do uit+=("$(plugin_naam "$d")"); done
    printf '%s' "${uit[*]:-}"
}

# Compose-bestand dat de plug-in-mappen in de hulpcontainers zet (tests en profielen).
schrijf_plugin_compose() {
    local d naam f="$STATE_DIR/$STACK.plugins.yml"
    PLUGIN_COMPOSE=""
    [ ${#PLUGIN_DIRS[@]} -gt 0 ] || return 0
    mkdir -p "$STATE_DIR"
    {
        echo "# Gegenereerd door scripts/stack.sh: plug-ins van stack $STACK. Niet bewerken."
        echo "services:"
        for svc in tools respect; do
            echo "  $svc:"
            echo "    environment:"
            echo "      DEMOSTACK_PLUGINS: \"$DEMOSTACK_PLUGINS\""
            echo "    volumes:"
            for d in "${PLUGIN_DIRS[@]}"; do
                naam="$(plugin_naam "$d")"
                echo "      - \"$d:/plugins/$naam:ro\""
            done
        done
    } > "$f"
    PLUGIN_COMPOSE="$f"
}

envwaarde() { python3 "$ROOT/scripts/lib/env.py" get "$1" 2>/dev/null || true; }

compose() {
    local bestanden=(-f "$STACKS/basis/compose.yml") f
    for f in $STACK_COMPOSE; do
        bestanden+=(-f "$ROOT/$f")
    done
    for f in "${PLUGIN_DIRS[@]}"; do
        bestanden+=(-f "$f/compose.yml")
        [ -f "$f/stacks/$STACK.yml" ] && bestanden+=(-f "$f/stacks/$STACK.yml")
    done
    [ -n "${PLUGIN_COMPOSE:-}" ] && bestanden+=(-f "$PLUGIN_COMPOSE")
    docker compose -p "$PROJECT" --project-directory "$ROOT" --env-file "$ROOT/.env" "${bestanden[@]}" "$@"
}

# Maakt .env aan of vult hem aan: elke sleutel uit .env.example en uit
# stacks/<naam>/env.example die nog ontbreekt, komt erbij. "__GENEREER__" wordt een
# nieuw willekeurig geheim. Bestaande waarden blijven staan.
zorg_voor_env() {
    local voorbeeld regel sleutel nieuw=0
    if [ ! -f "$ROOT/.env" ]; then
        info ".env bestaat nog niet: aanmaken met nieuwe geheimen (alleen lokaal gebruiken)"
        : > "$ROOT/.env"
        chmod 600 "$ROOT/.env"
    fi
    local plugin_voorbeelden=() d
    for d in "${PLUGIN_DIRS[@]}"; do plugin_voorbeelden+=("$d/env.example"); done
    for voorbeeld in "$ROOT/.env.example" "$STACK_DIR/env.example" "${plugin_voorbeelden[@]}"; do
        [ -f "$voorbeeld" ] || continue
        while IFS= read -r regel || [ -n "$regel" ]; do
            [[ "$regel" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue
            sleutel="${regel%%=*}"
            grep -q "^${sleutel}=" "$ROOT/.env" && continue
            if [[ "$regel" == *"=__GENEREER__" ]]; then
                printf '%s=%s\n' "$sleutel" "$(openssl rand -hex 20)" >> "$ROOT/.env"
            else
                printf '%s\n' "$regel" >> "$ROOT/.env"
            fi
            nieuw=$((nieuw + 1))
        done < "$voorbeeld"
    done
    [ "$nieuw" -gt 0 ] && info "$nieuw sleutel(s) toegevoegd aan .env"
    return 0
}

# Projecten van de demogemeente die nu containers hebben (draaiend of gestopt).
draaiende_stacks() {
    docker ps -a --format '{{.Label "com.docker.compose.project"}}' \
        | grep '^demogemeente' | sort -u || true
}

# Wacht tot alle langlopende containers healthy (of running zonder healthcheck) zijn.
wacht_op_gezond() {
    local max="${1:-900}" start nu niet_klaar
    start=$(date +%s)
    while true; do
        niet_klaar=$(compose ps --format '{{.Service}} {{.State}} {{.Health}}' \
            | awk '$2!="running" || ($3!="" && $3!="healthy") {print $1"("$2","$3")"}' \
            | grep -v -- '-init(exited' || true)
        if [ -z "$niet_klaar" ]; then
            info "alle services zijn gezond"
            return 0
        fi
        nu=$(date +%s)
        if [ $((nu - start)) -gt "$max" ]; then
            fout "na ${max}s nog niet gezond: $niet_klaar"
            return 1
        fi
        sleep 5
    done
}
