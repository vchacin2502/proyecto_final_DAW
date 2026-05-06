#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/www/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"
DOMAIN_DEFAULT="cafit.freemyip.com"

cd "$PROJECT_ROOT"

if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    echo "Se creo .env desde .env.example. Editalo y vuelve a ejecutar."
    exit 1
  else
    echo "No existe .env ni .env.example"
    exit 1
  fi
fi

set -a
source <(sed 's/\r$//' "$ENV_FILE")
set +a

DOMAIN="${DOMAIN:-$DOMAIN_DEFAULT}"

mkdir -p "$PROJECT_ROOT/www/certbot/www"
mkdir -p "$PROJECT_ROOT/www/certbot/conf/live/$DOMAIN"
mkdir -p "$PROJECT_ROOT/staticfiles"

if [ ! -f "$PROJECT_ROOT/www/certbot/conf/live/$DOMAIN/fullchain.pem" ] || [ ! -f "$PROJECT_ROOT/www/certbot/conf/live/$DOMAIN/privkey.pem" ]; then
  openssl req -x509 -newkey rsa:4096 -nodes \
    -out "$PROJECT_ROOT/www/certbot/conf/live/$DOMAIN/fullchain.pem" \
    -keyout "$PROJECT_ROOT/www/certbot/conf/live/$DOMAIN/privkey.pem" \
    -days 1 \
    -subj "/CN=$DOMAIN"
fi

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down --remove-orphans
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --build

echo "Despliegue levantado. Verifica con:"
echo "docker compose -f $COMPOSE_FILE --env-file $ENV_FILE ps"
