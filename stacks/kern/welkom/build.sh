#!/usr/bin/env bash
# Bouwt welkom/index.html uit de template. Gebruik: KISS=1 ./welkom/build.sh als KISS draait.
set -euo pipefail
cd "$(dirname "$0")"; . ../.env
if [ "${KISS:-0}" = 1 ]; then
  LINK="<a class=\"btn\" data-shot=\"kcc-1.jpg\" href=\"https://kiss.$BASE_DOMAIN/\">Open KISS <small>werkplek KCC</small></a>"
  STATE='<span class="state ok">Draait</span>'; VER="${KISS_VERSION:-}"
else
  LINK='<span class="btn off">KISS <small>wordt ingericht</small></span>'
  STATE='<span class="state soon">Wordt ingericht</span>'; VER="-"
fi
sed -e "s#__BASE__#$BASE_DOMAIN#g" -e "s#__KISS_LINK__#$LINK#" -e "s#__KISS_STATE__#$STATE#" -e "s#__KISS_VERSION__#$VER#" \
  index.template.html > public/index.html
