#!/usr/bin/env bash
# Print een Caddyfile voor deze stack. Gebruik: ./scripts/caddyfile.sh > /etc/caddy/Caddyfile && systemctl reload caddy
set -euo pipefail
cd "$(dirname "$0")/.."; . ./.env
HASH=$(caddy hash-password --plaintext "$ADMIN_PASSWORD")
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
for pair in zaken:8101 klant:8102 objecten:8103 objecttypen:8104 formulieren:8105 keycloak:8107 kiss:8108 gzac:8109; do
  printf '%s.%s {\n\timport proxy\n\treverse_proxy 127.0.0.1:%s\n}\n' "${pair%%:*}" "$BASE_DOMAIN" "${pair##*:}"
done
printf 'mail.%s {\n\timport proxy\n\tbasic_auth {\n\t\tadmin %s\n\t}\n\treverse_proxy 127.0.0.1:8106\n}\n' "$BASE_DOMAIN" "$HASH"
