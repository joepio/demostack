# syntax=docker/dockerfile:1
# OpenPlan 0.1.0 (maykinmedia/open-plan) heeft geen gepubliceerd image en geen git-tags;
# stacks/vcg/bouw.sh bouwt een vaste commit. Het Dockerfile van het project installeert
# systeempakketten met apt-get (Debian-spiegels zijn hier niet bereikbaar). Daarom staat
# OpenPlan hier op het image van Open Organisatie 0.2.0: hetzelfde Maykin-sjabloon
# (Python 3.12, uWSGI, gettext, postgresql-client, gebruiker maykin). Alleen de
# Python-pakketten (PyPI) en de frontend (npm) worden opnieuw geinstalleerd.
ARG NODE_IMAGE=node:22.22.0-alpine
ARG BASIS_IMAGE=maykinmedia/open-organisatie:0.2.0

FROM ${NODE_IMAGE} AS frontend
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt NPM_CONFIG_UPDATE_NOTIFIER=false CI=true
WORKDIR /app
COPY --from=bron build /app/build/
COPY --from=bron package.json package-lock.json webpack.config.js postcss.config.js karma.conf.js .babelrc /app/
RUN --mount=type=cache,id=demogemeente-npm,target=/root/.npm npm ci --no-audit --no-fund
COPY --from=bron src /app/src
RUN npm run build

FROM ${BASIS_IMAGE}
USER root
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; cat /etc/ssl/certs/ca-certificates.crt > /tmp/ca.crt; \
    for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /tmp/ca.crt || true; done
COPY --from=bron requirements /tmp/requirements
# uWSGI staat al in het basisimage (2.0.30) en zou hier gecompileerd moeten worden
RUN --mount=type=cache,id=demogemeente-pip,target=/root/.cache/pip \
    grep -v -i '^uwsgi==' /tmp/requirements/base.txt > /tmp/requirements/zonder-uwsgi.txt \
 && PIP_CERT=/tmp/ca.crt pip install -r /tmp/requirements/zonder-uwsgi.txt \
 && rm -rf /tmp/requirements /tmp/ca.crt /tmp/extra-ca
RUN rm -rf /app/src /app/static /app/node_modules
COPY --from=bron bin/docker_start.sh /start.sh
COPY --from=bron bin/uwsgi.ini /uwsgi.ini
COPY --from=bron bin/celery_worker.sh /celery_worker.sh
COPY --from=bron src /app/src
COPY --from=frontend /app/src/openplan/static /app/src/openplan/static
COPY --from=frontend /app/node_modules/@fortawesome/fontawesome-free/webfonts /app/node_modules/@fortawesome/fontawesome-free/webfonts
RUN chmod +x /start.sh /celery_worker.sh && chown -R maykin:maykin /app
USER maykin
ARG COMMIT_HASH=onbekend
ENV RELEASE=0.1.0 GIT_SHA=${COMMIT_HASH} PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=openplan.conf.docker
RUN SECRET_KEY=bouw python src/manage.py collectstatic --noinput \
 && SECRET_KEY=bouw python src/manage.py compilemessages
EXPOSE 8000
CMD ["/start.sh"]
