#!/usr/bin/env bash
# Schakel werkplekken (compose-profielen) aan of uit. De registers draaien altijd.
#   ./scripts/stack.sh status            welke profielen staan aan
#   ./scripts/stack.sh aan gzac          profiel erbij aanzetten
#   ./scripts/stack.sh uit kcc           profiel uitzetten
#   ./scripts/stack.sh alleen gzac       alleen dit profiel aan (naast de registers)
#   ./scripts/stack.sh toepassen         zet de profielen uit .env (COMPOSE_PROFILES) door
# Profielen: kcc (KISS, Elasticsearch, BRP-mock), gzac (GZAC/Valtimo), zac (ZAC van Dimpact met Solr, OPA, PABC),
#            oip (Open Inwoner), nlportal (NL Portal), mijnoverheid (MijnOverheid-demo VNG API Lab), iko (IKO)
set -euo pipefail
cd "$(dirname "$0")/.."
ALL="kcc gzac zac oip nlportal mijnoverheid iko"
cur=$(grep '^COMPOSE_PROFILES=' .env | cut -d= -f2 | tr ',' ' ')
want="$cur"
case "${1:-status}" in
  status) ;;
  toepassen) ;;
  aan)    want="$cur ${2:?profiel}" ;;
  uit)    want=$(echo "$cur" | tr ' ' '\n' | grep -vx "${2:?profiel}" | tr '\n' ' ') ;;
  alleen) want="${2:?profiel}" ;;
  *) sed -n '2,9p' "$0"; exit 1 ;;
esac
want=$(echo $want | tr ' ' '\n' | grep -E "^($(echo $ALL | tr ' ' '|'))$" | sort -u | tr '\n' ',' | sed 's/,$//')
if [ "${1:-status}" != status ]; then
  sed -i "s/^COMPOSE_PROFILES=.*/COMPOSE_PROFILES=$want/" .env
  for p in $ALL; do
    if ! echo ",$want," | grep -q ",$p,"; then
      svcs=$(comm -13 <(docker compose --profile '' config --services | sort) <(docker compose --profile "$p" config --services | sort))
      [ -n "$svcs" ] && docker compose --profile "$p" stop $svcs >/dev/null 2>&1 || true
    fi
  done
  docker compose up -d 2>&1 | grep -E "Started|Created" || true
  python3 welkom/evaluatie.py || true
  KISS=1 KISS_VERSION=3.2.0 ./welkom/build.sh
fi
echo "Aan: ${want:-alleen de registers}"
for p in $ALL; do echo ",$want," | grep -q ",$p," && echo "  $p: aan" || echo "  $p: uit"; done
