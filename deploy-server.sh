#!/bin/bash
set -euo pipefail

cd /opt/stacks/airsync

# Deszyfruj sekrety
sops --config /dev/null --input-type dotenv --output-type dotenv -d secrets.enc.env > .env
chmod 600 .env

# Pull i restart
docker compose pull
docker compose up -d

echo "==> Airsync deployed. Checking status..."
docker compose ps
