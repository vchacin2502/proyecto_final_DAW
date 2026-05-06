#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/www/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

cd "$PROJECT_ROOT"

if [ ! -f "$ENV_FILE" ]; then
  echo "Falta .env en la raiz del proyecto"
  exit 1
fi

set -a
source <(sed 's/\r$//' "$ENV_FILE")
set +a

DOMAIN="${1:-${DOMAIN:-cafit.freemyip.com}}"
EMAIL="${2:-${EMAIL_CERT:-}}"

if [ -n "$EMAIL" ]; then
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint certbot certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --non-interactive \
    --agree-tos \
    --no-eff-email \
    --force-renewal
else
  docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint certbot certbot certonly \
    --webroot -w /var/www/certbot \
    -d "$DOMAIN" \
    --non-interactive \
    --register-unsafely-without-email \
    --agree-tos \
    --force-renewal
fi

LATEST_CERT_DIR="$(ls -d "$PROJECT_ROOT/www/certbot/conf/live/${DOMAIN}"* 2>/dev/null | sort | tail -n1)"
if [ -z "$LATEST_CERT_DIR" ]; then
  echo "No se encontro certificado emitido para $DOMAIN"
  exit 1
fi

LATEST_CERT_BASENAME="$(basename "$LATEST_CERT_DIR")"
sed -i "s|^\s*ssl_certificate\s\+.*;|        ssl_certificate /etc/letsencrypt/live/${LATEST_CERT_BASENAME}/fullchain.pem;|" "$PROJECT_ROOT/www/nginx.conf"
sed -i "s|^\s*ssl_certificate_key\s\+.*;|        ssl_certificate_key /etc/letsencrypt/live/${LATEST_CERT_BASENAME}/privkey.pem;|" "$PROJECT_ROOT/www/nginx.conf"

docker exec contenedor_nginx nginx -s reload

echo "Certificado emitido y Nginx recargado para $DOMAIN usando ${LATEST_CERT_BASENAME}"
