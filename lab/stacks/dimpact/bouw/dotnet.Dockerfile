# syntax=docker/dockerfile:1
# Bouwt een .NET 8-component van PodiumD uit de broncode (ghcr.io is hier niet
# bereikbaar). Gebruikt door stacks/dimpact/bouw.sh, met twee benoemde contexten:
#   bron      de git-checkout van het component op de vaste tag
#   extra-ca  map met extra CA-certificaten (*.crt), leeg op een normale machine
# Alles op Alpine, zodat de images de basislagen delen.
ARG SDK_IMAGE=mcr.microsoft.com/dotnet/sdk:8.0.425-alpine3.24
ARG RUNTIME_IMAGE=mcr.microsoft.com/dotnet/aspnet:8.0.31-alpine3.24

FROM node:22.22.0-alpine AS node

FROM ${SDK_IMAGE} AS build
COPY --from=extra-ca . /tmp/extra-ca/
RUN set -e; for f in /tmp/extra-ca/*.crt; do [ -f "$f" ] && cat "$f" >> /etc/ssl/certs/ca-certificates.crt || true; done
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt \
    DOTNET_CLI_TELEMETRY_OPTOUT=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_AUDIT=false
# Node voor de Vue-frontends (de JavaScript-SDK van .NET roept npm aan bij publish)
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && node --version && npm --version
WORKDIR /src
COPY --from=bron . .
ARG PROJECT
ARG VERSION=0.0.0
RUN dotnet publish "$PROJECT" -c Release -o /app/publish /p:UseAppHost=false /p:Version=${VERSION}
# Losse frontend (KISS): npm ci en vite build in FRONTEND_DIR, resultaat in wwwroot
ARG FRONTEND_DIR=
RUN if [ -n "$FRONTEND_DIR" ]; then \
      cd "$FRONTEND_DIR" && npm ci && npx vite build && mkdir -p /app/publish/wwwroot && cp -r dist/. /app/publish/wwwroot/; \
    fi

FROM ${RUNTIME_IMAGE}
ENV ASPNETCORE_HTTP_PORTS=8080
WORKDIR /app
COPY --from=build /app/publish .
ARG DLL
ENV APP_DLL=${DLL}
USER $APP_UID
EXPOSE 8080
ENTRYPOINT ["sh", "-c", "exec dotnet \"$APP_DLL\""]
