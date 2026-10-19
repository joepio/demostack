#!/usr/bin/env bash
# Bouwt de PodiumD-componenten die alleen op ghcr.io staan uit hun broncode, op de tag
# uit de PodiumD-chart 4.9.3. Alleen images die nog niet bestaan worden gebouwd.
# scripts/stack.sh up dimpact roept dit aan; los: stacks/dimpact/bouw.sh [naam...]
#
# Achter een proxy met TLS-inspectie: EXTRA_CA_CERT=/pad/naar/ca.crt (wordt in de
# bouwfase vertrouwd, niet in het eindimage).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BRON="${DEMO_BRON_DIR:-$ROOT/.bron}"
DOCKERFILE="$ROOT/stacks/dimpact/bouw/dotnet.Dockerfile"

# naam | repository | tag | project (.csproj) | dll | losse frontend-map
COMPONENTEN=(
  "pabc-api|https://github.com/Platform-Autorisatie-Beheer-Component/pabc-api|v1.1.1|PABC.Server/PABC.Server.csproj|PABC.Server.dll|"
  "pabc-migrations|https://github.com/Platform-Autorisatie-Beheer-Component/pabc-api|v1.1.1|PABC.MigrationService/PABC.MigrationService.csproj|PABC.MigrationService.dll|"
  "ita-web|https://github.com/Interne-Taak-Afhandeling/ITA|v3.3.2|InterneTaakAfhandeling.Web.Server/InterneTaakAfhandeling.Web.Server.csproj|InterneTaakAfhandeling.Web.Server.dll|"
  "ita-poller|https://github.com/Interne-Taak-Afhandeling/ITA|v3.3.2|InterneTaakAfhandeling.Poller/InterneTaakAfhandeling.Poller.csproj|InterneTaakAfhandeling.Poller.dll|"
  "kiss|https://github.com/Klantinteractie-Servicesysteem/KISS-frontend|v3.1.3|Kiss.Bff/Kiss.Bff.csproj|Kiss.Bff.dll|."
)

# TLS voor Keycloak binnen het docker-netwerk: KISS en ITA eisen een OIDC-authority met
# https (RequireHttpsMetadata staat vast aan). Eigen demo-CA, alleen voor keycloak.local;
# niet in git (stacks/dimpact/.tls/ staat in .gitignore).
TLS="$ROOT/stacks/dimpact/.tls"
if [ ! -s "$TLS/keycloak.crt" ]; then
    echo "==> demo-CA en certificaat voor keycloak.local maken ($TLS)"
    mkdir -p "$TLS"
    openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=Demogemeente Voorbeeldstad demo-CA" \
        -keyout "$TLS/ca.key" -out "$TLS/ca.crt" 2>/dev/null
    openssl req -newkey rsa:2048 -nodes -subj "/CN=keycloak.local" \
        -keyout "$TLS/keycloak.key" -out "$TLS/keycloak.csr" 2>/dev/null
    printf 'subjectAltName=DNS:keycloak.local,DNS:keycloak\nextendedKeyUsage=serverAuth\n' > "$TLS/ext.cnf"
    openssl x509 -req -in "$TLS/keycloak.csr" -CA "$TLS/ca.crt" -CAkey "$TLS/ca.key" -CAcreateserial \
        -days 825 -extfile "$TLS/ext.cnf" -out "$TLS/keycloak.crt" 2>/dev/null
    # Keycloak draait als uid 1000 en moet de sleutel kunnen lezen (alleen een demo)
    chmod 644 "$TLS/keycloak.key" "$TLS/keycloak.crt" "$TLS/ca.crt"
    rm -f "$TLS/keycloak.csr" "$TLS/ext.cnf"
fi

ca_dir="$(mktemp -d)"
trap 'rm -rf "$ca_dir"' EXIT
if [ -n "${EXTRA_CA_CERT:-}" ]; then
    cp "$EXTRA_CA_CERT" "$ca_dir/extra.crt"
fi

for regel in "${COMPONENTEN[@]}"; do
    IFS='|' read -r naam repo tag project dll frontend <<< "$regel"
    if [ $# -gt 0 ] && ! printf '%s\n' "$@" | grep -qx "$naam"; then
        continue
    fi
    image="demogemeente/$naam:${tag#v}"
    if docker image inspect "$image" >/dev/null 2>&1; then
        echo "bestaat al: $image"
        continue
    fi
    checkout="$BRON/$(basename "$repo")-$tag"
    if [ ! -d "$checkout/.git" ]; then
        git clone -q --depth 1 -b "$tag" "$repo" "$checkout"
    fi
    echo "==> bouwen: $image (uit $repo $tag)"
    docker build -f "$DOCKERFILE" \
        --build-context bron="$checkout" \
        --build-context extra-ca="$ca_dir" \
        --build-arg PROJECT="$project" \
        --build-arg DLL="$dll" \
        --build-arg FRONTEND_DIR="$frontend" \
        --build-arg VERSION="${tag#v}" \
        -t "$image" "$ROOT/stacks/dimpact/bouw"
done
