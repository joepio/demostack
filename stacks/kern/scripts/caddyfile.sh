#!/usr/bin/env bash
# Print een Caddyfile voor deze stack. Gebruik: ./scripts/caddyfile.sh > /etc/caddy/Caddyfile && systemctl reload caddy
set -euo pipefail
cd "$(dirname "$0")/.."; . ./.env
WELKOM="$(pwd)/welkom/public"
[ -n "${ACME_EMAIL:-}" ] && printf '{\n\temail %s\n}\n\n' "$ACME_EMAIL"
cat <<CADDY
(proxy) {
	encode zstd gzip
	header -Server
}

$BASE_DOMAIN {
	import proxy
	root * $WELKOM
	file_server
}
CADDY
for pair in zaken:8101 klant:8102 objecten:8103 objecttypen:8104 formulieren:8105 kiss:8108 gzac:8109 notificaties:8110 zac:8111 pabc:8112 inwoner:8113 iko:8116 mijnoverheid:8117; do
  printf '%s.%s {\n\timport proxy\n\treverse_proxy 127.0.0.1:%s\n}\n' "${pair%%:*}" "$BASE_DOMAIN" "${pair##*:}"
done
# NL Portal: frontend en backend op één adres; de nginx in het frontend-image verwacht de backend op localhost
printf 'portaal.%s {\n\timport proxy\n\t@api path /graphql* /api/*\n\treverse_proxy @api 127.0.0.1:8115\n\treverse_proxy 127.0.0.1:8114\n}\n' "$BASE_DOMAIN"
# ZaakChat: /koppeling (inloggen via Keycloak, notificaties) naar de koppeling, de rest naar ZaakChat zelf
printf 'zaakchat.%s {\n\timport proxy\n\treverse_proxy /koppeling/* 127.0.0.1:8119\n\treverse_proxy 127.0.0.1:8118\n}\n' "$BASE_DOMAIN"
# Keycloak, met /demo-login (inloggen zonder wachtwoord voor demo-accounts) op hetzelfde adres vanwege de sessiecookies
printf 'keycloak.%s {\n\timport proxy\n\treverse_proxy /demo-login* 127.0.0.1:8120\n\treverse_proxy 127.0.0.1:8107\n}\n' "$BASE_DOMAIN"
# OneGround: elke ZGW-API op een eigen adres (de API's staan op /api/v1); Keycloak zonder beheerconsole
for pair in autorisaties:8130 catalogi:8131 zaken:8132 documenten:8133 besluiten:8134 notificaties:8135 referentielijsten:8136; do
  printf 'og-%s.%s {\n\timport proxy\n\treverse_proxy 127.0.0.1:%s\n}\n' "${pair%%:*}" "$BASE_DOMAIN" "${pair##*:}"
done
printf 'og-keycloak.%s {\n\timport proxy\n\trespond /admin* 403\n\treverse_proxy 127.0.0.1:8137\n}\n' "$BASE_DOMAIN"
# Mailpit bevat alleen demomail; geen apart wachtwoord nodig
printf 'mail.%s {\n\timport proxy\n\treverse_proxy 127.0.0.1:8106\n}\n' "$BASE_DOMAIN"

# Oude adressen (bijv. na een domeinwissel) doorverwijzen naar hetzelfde onderdeel op het nieuwe domein
for old in ${OUD_DOMEIN:-}; do
  printf '%s {\n\tredir https://%s{uri} 308\n}\n' "$old" "$BASE_DOMAIN"
  for sub in zaken klant objecten objecttypen formulieren keycloak kiss gzac notificaties zac pabc portaal inwoner iko mijnoverheid zaakchat mail; do
    printf '%s.%s {\n\tredir https://%s.%s{uri} 308\n}\n' "$sub" "$old" "$sub" "$BASE_DOMAIN"
  done
done
