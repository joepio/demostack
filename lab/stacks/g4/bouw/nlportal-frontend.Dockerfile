# syntax=docker/dockerfile:1
# Bouwt de voorbeeld-app van de NL Portal-frontendbibliotheken (packages/app) en serveert
# die met nginx. config.js wordt bij het starten uit omgevingsvariabelen geschreven
# (stacks/g4/bouw/nlportal-config.sh), zoals config.template.js van het project bedoelt.
ARG NODE_IMAGE=node:22.22.0-alpine
ARG NGINX_IMAGE=nginx:1.29.8-alpine

FROM ${NODE_IMAGE} AS build
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    HUSKY=0 \
    CI=true
RUN npm install -g pnpm@10.18.3 >/dev/null
WORKDIR /src
COPY --from=bron . .
RUN --mount=type=cache,id=demogemeente-pnpm,target=/root/.local/share/pnpm/store \
    pnpm install --frozen-lockfile
RUN pnpm run --recursive --filter "./packages/*" --filter "!@nl-portal/nl-portal-app" build \
 && cd packages/app && npx tsc && npx vite build

FROM ${NGINX_IMAGE}
COPY --from=build /src/packages/app/dist /usr/share/nginx/html
COPY nlportal-nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=755 nlportal-config.sh /docker-entrypoint.d/40-nlportal-config.sh
EXPOSE 8080
