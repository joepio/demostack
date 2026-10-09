#!/usr/bin/env bash
# Maakt de screenshots voor de welkomstpagina in public/shots/ (met de Playwright-container).
set -euo pipefail
cd "$(dirname "$0")"; set -a; . ../.env; set +a
mkdir -p public/shots
docker run --rm --network host -e BASE_DOMAIN -e ADMIN_PASSWORD \
  -v "$PWD/screenshots.py:/s.py:ro" -v "$PWD/public/shots:/out" \
  mcr.microsoft.com/playwright/python:v1.55.0-noble \
  sh -c "pip -q install playwright==1.55.0 2>/dev/null; python /s.py"
chmod -R a+rX public/shots
