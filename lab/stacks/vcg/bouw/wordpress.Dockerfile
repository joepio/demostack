# syntax=docker/dockerfile:1
# WordPress 6.8.3 met de OpenWebconcept-plugins uit de VCG-basisset:
#   OpenPDC (plugin-pdc-base 3.18.1)   producten- en dienstencatalogus met REST-API
#   OpenPub (plugin-openpub-base 3.8.7) nieuwsberichten en publicaties met REST-API
# en wat die plugins vereisen: Meta Box 5.10.10, CMB2 2.11.0 en Posts 2 Posts 1.6.5
# (koppelingen tussen PDC-items en thema's), alle uit GitHub, plus de
# Composer-afhankelijkheden. wordpress.org (plugin-directory, wp-cli-downloads) is hier
# niet bereikbaar; daarom komt alles uit GitHub en Packagist.
#
# Meta Box Group (vereist door OpenPDC) staat alleen op wordpress.org en metabox.io; in
# plaats daarvan staat hier een kleine vervanger (wordpress/meta-box-group/), zie
# stacks/vcg/README.md.
ARG COMPOSER_IMAGE=composer:2.8.12
ARG WP_IMAGE=wordpress:6.8.3-php8.3-apache
ARG WPCLI_IMAGE=wordpress:cli-2.12.0-php8.3

FROM ${COMPOSER_IMAGE} AS composer
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_NO_INTERACTION=1
WORKDIR /plugins
COPY --from=pdc . pdc-base/
COPY --from=openpub . openpub-base/
COPY --from=metabox . meta-box/
COPY --from=cmb2 . cmb2/
COPY --from=p2p . posts-to-posts/
# GitHub-zips (api.github.com) zijn hier niet bereikbaar: Composer installeert dan uit git
RUN --mount=type=cache,id=demogemeente-composer,target=/tmp/cache \
    set -e; export COMPOSER_CACHE_DIR=/tmp/cache; \
    for p in pdc-base openpub-base meta-box posts-to-posts; do \
      (cd "$p" && composer install --no-dev --prefer-source --no-scripts --optimize-autoloader --ignore-platform-reqs); \
    done; \
    find /plugins -name .git -prune -exec rm -rf {} +; \
    rm -rf /plugins/*/tests /plugins/*/.github

FROM ${WPCLI_IMAGE} AS wpcli

FROM ${WP_IMAGE}
COPY --from=wpcli /usr/local/bin/wp /usr/local/bin/wp
COPY --from=composer /plugins/ /usr/src/wordpress/wp-content/plugins/
COPY wordpress/meta-box-group/ /usr/src/wordpress/wp-content/plugins/meta-box-group/
RUN chown -R www-data:www-data /usr/src/wordpress/wp-content/plugins
