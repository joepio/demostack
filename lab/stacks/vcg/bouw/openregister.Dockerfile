# syntax=docker/dockerfile:1
# Nextcloud 31 met de app OpenRegister (Conduction) op tag v1.0.3, de versie uit de
# VCG-basisset. De app store van Nextcloud (apps.nextcloud.com) is hier niet bereikbaar;
# daarom bouwt dit image de app uit de broncode: PHP-afhankelijkheden met Composer, de
# frontend met npm/webpack. Na de installatie zet nextcloud-hooks/ de app aan.
ARG NODE_IMAGE=node:22.22.0-alpine
ARG COMPOSER_IMAGE=composer:2.8.12
ARG NEXTCLOUD_IMAGE=nextcloud:31.0.9-apache

FROM ${NODE_IMAGE} AS frontend
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt NPM_CONFIG_UPDATE_NOTIFIER=false CI=true \
    NODE_OPTIONS=--max-old-space-size=3072
WORKDIR /app
COPY --from=bron package.json package-lock.json ./
# Zonder install-scripts (die halen binaire bestanden van buiten); vue-demi heeft zijn
# postinstall wel nodig om naar Vue 2.7 te wijzen, dus die apart
RUN --mount=type=cache,id=demogemeente-npm,target=/root/.npm npm ci --no-audit --no-fund --ignore-scripts \
 && npm rebuild vue-demi
COPY --from=bron . .
RUN npm run build

FROM ${COMPOSER_IMAGE} AS php
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_NO_INTERACTION=1
WORKDIR /app
COPY --from=bron . .
RUN --mount=type=cache,id=demogemeente-composer,target=/tmp/cache \
    COMPOSER_CACHE_DIR=/tmp/cache composer install --no-dev --prefer-source --no-scripts \
      --optimize-autoloader --ignore-platform-reqs \
 && rm -rf node_modules tests docs n8n-mcp n8n-templates exapps .git vendor-bin \
      composer.phar phpstan.phar *.yml *.yaml

FROM ${NEXTCLOUD_IMAGE}
COPY --from=php --chown=www-data:www-data /app /usr/src/nextcloud/custom_apps/openregister
COPY --from=frontend --chown=www-data:www-data /app/js /usr/src/nextcloud/custom_apps/openregister/js
COPY --chmod=755 nextcloud-hooks/ /docker-entrypoint-hooks.d/post-installation/
