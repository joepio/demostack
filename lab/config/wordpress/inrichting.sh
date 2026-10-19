#!/bin/bash
# Inrichting van WordPress met OpenPDC en OpenPub (stack vcg), idempotent. Draait met
# het image demogemeente/wordpress-owc (wp-cli) op het gedeelde volume /var/www/html,
# nadat de WordPress-container de bestanden heeft klaargezet.
#
# 1. WordPress installeren (titel, beheerder, Nederlands waar mogelijk, nette permalinks
#    zodat /wp-json/ werkt).
# 2. Plugins aanzetten: Meta Box (+ vervanger Meta Box Group), CMB2, Posts 2 Posts,
#    OpenPDC, OpenPub.
# 3. Inhoud van Voorbeeldstad: PDC-thema's en -items (producten en diensten) en
#    OpenPub-berichten. Alleen fictieve, openbare informatie: geen persoonsgegevens.
set -euo pipefail
WP="wp --allow-root --path=/var/www/html"
URL="http://localhost:${PORT_WORDPRESS:-8256}"

for i in $(seq 1 90); do
    [ -f /var/www/html/wp-config.php ] && php -r '$m = @new mysqli(getenv("WORDPRESS_DB_HOST"), getenv("WORDPRESS_DB_USER"), getenv("WORDPRESS_DB_PASSWORD"), getenv("WORDPRESS_DB_NAME")); exit($m->connect_errno ? 1 : 0);' && break
    sleep 2
done

if ! $WP core is-installed 2>/dev/null; then
    $WP core install --url="$URL" --title="${GEMEENTE_NAAM:-Gemeente Voorbeeldstad}" \
        --admin_user="${ADMIN_USERNAME:-admin}" --admin_password="$ADMIN_PASSWORD" \
        --admin_email="beheer@voorbeeldstad.example" --skip-email
fi
$WP option update blogdescription "Producten, diensten en nieuws (fictief)"
$WP option update timezone_string "Europe/Amsterdam"
$WP rewrite structure '/%postname%/' --hard >/dev/null
$WP plugin activate meta-box meta-box-group cmb2 posts-to-posts pdc-base openpub-base
# Posts 2 Posts maakt zijn tabellen (wp_p2p, wp_p2pmeta) pas bij een beheerpagina aan;
# via wp-cli expliciet, anders blijven koppelingen tussen items en thema's leeg
$WP eval 'if (class_exists("P2P_Storage")) { P2P_Storage::install(); }'

# Termen en berichten alleen aanmaken als ze er nog niet zijn (op slug)
post() {  # type slug titel inhoud [samenvatting]
    local id
    id=$($WP post list --post_type="$1" --name="$2" --field=ID --post_status=any | head -1)
    if [ -z "$id" ]; then
        id=$($WP post create --post_type="$1" --post_name="$2" --post_title="$3" --post_content="$4" \
            --post_excerpt="${5:-}" --post_status=publish --porcelain)
    fi
    echo "$id"
}

# OpenPDC: thema's (pdc-category) en items (pdc-item), gekoppeld via posts-to-posts
thema_parkeren=$(post pdc-category parkeren "Parkeren" "Alles over parkeren in Voorbeeldstad.")
thema_burgerzaken=$(post pdc-category burgerzaken "Burgerzaken" "Paspoort, rijbewijs en verhuizen.")
thema_zorg=$(post pdc-category zorg-en-ondersteuning "Zorg en ondersteuning" "Hulp via de Wmo.")
pv=$(post pdc-item parkeervergunning-bewoners "Parkeervergunning bewoners aanvragen" \
    "<p>Woont u in het vergunninggebied binnenstad? Dan kunt u een parkeervergunning aanvragen. Een vergunning kost 120 euro per jaar.</p><p>U vraagt de vergunning aan met DigiD.</p>" \
    "Vraag een parkeervergunning aan als u in de binnenstad woont.")
pp=$(post pdc-item paspoort-aanvragen "Paspoort aanvragen" \
    "<p>U vraagt een paspoort aan bij de balie van het stadskantoor. Maak eerst een afspraak.</p>" \
    "Een paspoort aanvragen bij de gemeente.")
wmo=$(post pdc-item huishoudelijke-hulp "Huishoudelijke hulp (Wmo)" \
    "<p>Lukt het huishouden niet meer zelf? Dan kunt u huishoudelijke hulp aanvragen via de Wmo.</p>" \
    "Hulp bij het huishouden via de Wmo.")
for paar in "$pv:$thema_parkeren" "$pp:$thema_burgerzaken" "$wmo:$thema_zorg"; do
    item="${paar%%:*}"; thema="${paar##*:}"
    $WP eval "if (function_exists('p2p_type') && p2p_type('pdc-item_to_pdc-category')) { p2p_type('pdc-item_to_pdc-category')->connect($item, $thema); }" >/dev/null 2>&1 || true
done
# Actief (anders laat de REST-API van OpenPDC het item weg) en de UPL-naam
# (Uniforme Productnamenlijst) als metadata op het item
for item in "$pv" "$pp" "$wmo"; do
    $WP post meta update "$item" _owc_pdc_active 1 >/dev/null
done
$WP post meta update "$pv" _owc_pdc_upl_naam "parkeervergunning" >/dev/null
$WP post meta update "$pp" _owc_pdc_upl_naam "paspoort" >/dev/null
$WP post meta update "$wmo" _owc_pdc_upl_naam "huishoudelijke hulp" >/dev/null

# OpenPub: nieuwsberichten
post openpub-item nieuwe-parkeertarieven-2026 "Nieuwe parkeertarieven binnenstad per 1 januari" \
    "<p>Het college heeft de parkeertarieven voor 2026 vastgesteld. Een bewonersvergunning kost 120 euro per jaar.</p>" \
    "De parkeertarieven in de binnenstad veranderen." >/dev/null
post openpub-item stadskantoor-feestdagen "Stadskantoor gesloten tijdens de feestdagen" \
    "<p>Op 25 en 26 december is het stadskantoor gesloten. Digitaal regelen kan altijd.</p>" \
    "Openingstijden rond de feestdagen." >/dev/null

echo "WordPress ingericht: OpenPDC ($($WP post list --post_type=pdc-item --format=count) items), OpenPub ($($WP post list --post_type=openpub-item --format=count) berichten)"
