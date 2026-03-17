#!/bin/bash
set -euo pipefail

REPO="ghcr.io/emssik/airsync"
TAG=$(date +%Y%m%d-%H%M)
SERVER="root@100.102.197.28"
STACK_DIR="/opt/stacks/airsync"

# Zaszyfruj .env kluczem publicznym serwera
AGE_KEY="age15y973cxq9kst6jfr7uhglt6msy5qwlp92vsn4ug28mhacx7zfqds8vqq6z"
sops --config /dev/null --input-type dotenv --output-type dotenv --age "$AGE_KEY" -e .env > secrets.enc.env

# Zbuduj i wypchnij obraz
echo "==> Build image tag: $TAG..."
docker build --platform linux/amd64 -f docker/Dockerfile.airsync -t "$REPO:latest" -t "$REPO:$TAG" .

echo "==> Push to GHCR..."
docker push "$REPO:latest"
docker push "$REPO:$TAG"

# Wyślij pliki na serwer i odpal deploy
echo "==> Deploy on server..."
ssh "$SERVER" "mkdir -p $STACK_DIR"
scp secrets.enc.env "$SERVER:$STACK_DIR/secrets.enc.env"
scp compose.prod.yaml "$SERVER:$STACK_DIR/compose.yaml"
scp deploy-server.sh "$SERVER:$STACK_DIR/deploy.sh"
ssh "$SERVER" "chmod +x $STACK_DIR/deploy.sh && cd $STACK_DIR && ./deploy.sh"

echo "==> Done! Tag: $TAG"
