#!/usr/bin/env bash
# Bouwt de VCG-componenten zonder bruikbaar image uit hun broncode, op een vaste versie:
#   openplan       OpenPlan 0.1.0 (maykinmedia/open-plan): geen image, geen git-tags;
#                  vaste commit uit de README-versie 0.1.0
#   wordpress      WordPress met OpenPDC 3.18.1 en OpenPub 3.8.7 (OpenWebconcept), hun
#                  vereiste plugins (Meta Box, CMB2, Posts 2 Posts) en de Composer-
#                  afhankelijkheden
#   openregister   Nextcloud met de app OpenRegister 1.0.3 (Conduction), met Composer-
#                  en npm-afhankelijkheden (de app store van Nextcloud is niet bereikbaar)
# en maakt eenmalig de test-PKI voor OpenFSC (fsc-pki.sh).
# Alleen images die nog niet bestaan worden gebouwd.
# scripts/stack.sh up vcg roept dit aan; los: stacks/vcg/bouw.sh [naam...]
#
# Achter een proxy met TLS-inspectie: EXTRA_CA_CERT=/pad/naar/ca.crt (alleen in de
# bouwfase vertrouwd, niet in het eindimage).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BRON="${DEMO_BRON_DIR:-$ROOT/.bron}"
BOUW="$ROOT/stacks/vcg/bouw"

# naam | image | Dockerfile | bronnen (contextnaam=repository@ref, spatiegescheiden)
COMPONENTEN=(
  "openplan|demogemeente/openplan:0.1.0|openplan.Dockerfile|bron=https://github.com/maykinmedia/open-plan@b1f945de592a5e5e0f1a6c993d30138db36eaa59"
  "wordpress|demogemeente/wordpress-owc:6.8.3|wordpress.Dockerfile|pdc=https://github.com/OpenWebconcept/plugin-pdc-base@v3.18.1 openpub=https://github.com/OpenWebconcept/plugin-openpub-base@v3.8.7 metabox=https://github.com/wpmetabox/meta-box@5.10.10 cmb2=https://github.com/CMB2/CMB2@v2.11.0 p2p=https://github.com/scribu/wp-posts-to-posts@1.6.5"
  "openregister|demogemeente/openregister:1.0.3|openregister.Dockerfile|bron=https://github.com/ConductionNL/openregister@v1.0.3"
)
BASIS=(node:22.22.0-alpine maykinmedia/open-organisatie:0.2.0 wordpress:6.8.3-php8.3-apache wordpress:cli-2.12.0-php8.3 composer:2.8.12 nextcloud:31.0.9-apache)

# Basisimages vooraf ophalen, met uitwijk naar mirror.gcr.io bij een 429 van Docker Hub
haal() {
    local pad
    docker image inspect "$1" >/dev/null 2>&1 && return 0
    docker pull -q "$1" >/dev/null 2>&1 && return 0
    case "$1" in */*) pad="$1" ;; *) pad="library/$1" ;; esac
    docker pull -q "mirror.gcr.io/$pad" >/dev/null && docker tag "mirror.gcr.io/$pad" "$1" \
        && docker rmi "mirror.gcr.io/$pad" >/dev/null
}

# Broncode op een vaste ref (tag of commit) ophalen in $BRON/<repo>-<ref>
checkout() {
    local repo="$1" ref="$2" dir
    dir="$BRON/$(basename "$repo")-$ref"
    if [ ! -d "$dir/.git" ]; then
        mkdir -p "$dir"
        git -C "$dir" init -q
        git -C "$dir" fetch -q --depth 1 "$repo" "$ref"
        git -C "$dir" -c advice.detachedHead=false checkout -q FETCH_HEAD
    fi
    echo "$dir"
}

# Test-PKI voor OpenFSC (eenmalig, idempotent)
"$ROOT/stacks/vcg/fsc-pki.sh"

ca_dir="$(mktemp -d)"
trap 'rm -rf "$ca_dir"' EXIT
if [ -n "${EXTRA_CA_CERT:-}" ]; then
    cp "$EXTRA_CA_CERT" "$ca_dir/extra.crt"
fi

for regel in "${COMPONENTEN[@]}"; do
    IFS='|' read -r naam image dockerfile bronnen <<< "$regel"
    if [ $# -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$naam"; then
        continue
    fi
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "bestaat al: $image"
        continue
    fi
    for b in "${BASIS[@]}"; do haal "$b"; done
    contexten=(--build-context extra-ca="$ca_dir")
    for bron in $bronnen; do
        ctx="${bron%%=*}"; rest="${bron#*=}"
        dir="$(checkout "${rest%@*}" "${rest##*@}")"
        contexten+=(--build-context "$ctx=$dir")
        [ "$ctx" = bron ] && commit="$(git -C "$dir" rev-parse --short HEAD)"
    done
    echo "==> bouwen: $image"
    DOCKER_BUILDKIT=1 docker build -f "$BOUW/$dockerfile" "${contexten[@]}" \
        --build-arg COMMIT_HASH="${commit:-onbekend}" -t "$image" "$BOUW"
done
