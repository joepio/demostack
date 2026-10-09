#!/bin/sh
# Na de eerste installatie van Nextcloud: OpenRegister aanzetten en Nextcloud bereikbaar
# maken onder de interne naam (seed, tests) en via localhost (browser).
set -e
php /var/www/html/occ app:enable openregister
php /var/www/html/occ config:system:set trusted_domains 1 --value=openregister.local
php /var/www/html/occ config:system:set trusted_domains 2 --value=openregister.local:80
php /var/www/html/occ config:system:set overwrite.cli.url --value="http://localhost:${PORT_NEXTCLOUD:-8257}"
php /var/www/html/occ background:cron
