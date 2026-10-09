#!/usr/bin/env bash
# Bouwt de G4-componenten zonder bereikbaar image uit hun broncode, op een vaste tag:
#   nlportal-backend   NL Portal is een set bibliotheken; Ritense publiceert geen
#                      backend-image. We bouwen de voorbeeld-app (module app) van
#                      nl-portal-backend-libraries.
#   nlportal-frontend  idem voor de frontend (packages/app), geserveerd met nginx.
#   iko                IKO 1.5.x staat alleen op ghcr.io, dat hier niet bereikbaar is.
# Alleen images die nog niet bestaan worden gebouwd.
# scripts/stack.sh up g4 roept dit aan; los: stacks/g4/bouw.sh [naam...]
#
# Achter een proxy met TLS-inspectie: EXTRA_CA_CERT=/pad/naar/ca.crt (alleen in de
# bouwfase vertrouwd, niet in het eindimage).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BRON="${DEMO_BRON_DIR:-$ROOT/.bron}"
BOUW="$ROOT/stacks/g4/bouw"

# naam | repository | tag | Dockerfile | Gradle-taak | jar
COMPONENTEN=(
  "nlportal-backend|https://github.com/nl-portal/nl-portal-backend-libraries|3.0.4.RELEASE|jvm.Dockerfile|:app:bootJar|app/build/libs/app-*.jar"
  "nlportal-frontend|https://github.com/nl-portal/nl-portal-frontend-libraries|v3.0.3|nlportal-frontend.Dockerfile||"
  "iko|https://github.com/Integraal-Klant-en-Objectbeeld/iko|v1.5.1|jvm.Dockerfile|bootJar|build/libs/iko.jar"
)
BASIS=(eclipse-temurin:21.0.12_8-jdk-alpine-3.23 eclipse-temurin:21.0.12_8-jre-alpine-3.23 node:22.22.0-alpine nginx:1.29.8-alpine)

# Basisimages vooraf ophalen, met uitwijk naar mirror.gcr.io bij een 429 van Docker Hub
haal() {
    docker image inspect "$1" >/dev/null 2>&1 && return 0
    docker pull -q "$1" >/dev/null 2>&1 && return 0
    docker pull -q "mirror.gcr.io/library/$1" >/dev/null && docker tag "mirror.gcr.io/library/$1" "$1" \
        && docker rmi "mirror.gcr.io/library/$1" >/dev/null
}

# Sleutels met een vaste lengte, die env.example (40 hex-tekens) niet kan maken:
#   IKO_CRYPTO_KEY                 AES-256-sleutel in Base64 (versleuteling van connectorgeheimen)
#   GZAC_PLUGIN_ENCRYPTIESLEUTEL   16 tekens (AES-128, versleuteling van plugingeheimen in GZAC)
if [ -f "$ROOT/.env" ]; then
    grep -q '^IKO_CRYPTO_KEY=' "$ROOT/.env" || echo "IKO_CRYPTO_KEY=$(openssl rand -base64 32)" >> "$ROOT/.env"
    grep -q '^GZAC_PLUGIN_ENCRYPTIESLEUTEL=' "$ROOT/.env" || echo "GZAC_PLUGIN_ENCRYPTIESLEUTEL=$(openssl rand -hex 8)" >> "$ROOT/.env"
fi

ca_dir="$(mktemp -d)"
trap 'rm -rf "$ca_dir"' EXIT
if [ -n "${EXTRA_CA_CERT:-}" ]; then
    cp "$EXTRA_CA_CERT" "$ca_dir/extra.crt"
fi

for regel in "${COMPONENTEN[@]}"; do
    IFS='|' read -r naam repo tag dockerfile taak jar <<< "$regel"
    if [ $# -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$naam"; then
        continue
    fi
    versie="${tag#v}"; versie="${versie%.RELEASE}"
    image="demogemeente/$naam:$versie"
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "bestaat al: $image"
        continue
    fi
    for b in "${BASIS[@]}"; do haal "$b"; done
    checkout="$BRON/$(basename "$repo")-$tag"
    if [ ! -d "$checkout/.git" ]; then
        git clone -q --depth 1 -b "$tag" "$repo" "$checkout"
    fi
    echo "==> bouwen: $image (uit $repo $tag)"
    DOCKER_BUILDKIT=1 docker build -f "$BOUW/$dockerfile" \
        --build-context bron="$checkout" \
        --build-context extra-ca="$ca_dir" \
        --build-arg GRADLE_TAAK="$taak" \
        --build-arg JAR_PAD="$jar" \
        -t "$image" "$BOUW"
done
