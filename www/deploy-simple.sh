#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "=== DESPLIEGUE SIMPLE CAFIT ==="

# 1) Crear directorios
mkdir -p www/certbot/www/.well-known/acme-challenge
mkdir -p www/certbot/conf/live/cafit.freemyip.com

# 2) Crear certificado temporal si no existe
if [ ! -f "www/certbot/conf/live/cafit.freemyip.com/fullchain.pem" ]; then
  echo "Creando certificado temporal..."
  openssl req -x509 -newkey rsa:4096 -nodes \
    -out www/certbot/conf/live/cafit.freemyip.com/fullchain.pem \
    -keyout www/certbot/conf/live/cafit.freemyip.com/privkey.pem \
    -days 1 -subj "/CN=cafit.freemyip.com"
fi

# 3) Limpiar CRLF si viene de Windows
sed -i 's/\r$//' .env www/*.sh

# 4) Levantar stack
echo "Levantando contenedores..."
docker compose -f www/docker-compose.yml --env-file .env down 2>/dev/null || true
docker compose -f www/docker-compose.yml --env-file .env up -d

echo "Esperando 15 segundos..."
sleep 15

# 5) Intentar certificado real
echo "Intentando certificado real..."
docker compose -f www/docker-compose.yml --env-file .env exec -T certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d cafit.freemyip.com \
  --email admin@cafit.freemyip.com \
  --non-interactive --agree-tos --no-eff-email \
  2>/dev/null || echo "SSL real no disponible aún (probablemente DNS/puerto 80)"

# 6) Recargar nginx
docker exec contenedor_nginx nginx -s reload 2>/dev/null || true

echo ""
echo "=== LISTO ==="
echo "Estado:"
docker compose -f www/docker-compose.yml --env-file .env ps
echo ""
echo "Prueba:"
echo "  curl -k -I https://cafit.freemyip.com"
