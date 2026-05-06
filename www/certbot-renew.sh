#!/bin/bash

# Script para generar certificados SSL reales con Certbot
# Ejecutar DESPUÉS de que todos los contenedores estén corriendo

DOMAIN=${1:-cafit.freemyip.com}
EMAIL=${2:-admin@example.com}

echo "======================================"
echo "Generando certificados reales para: $DOMAIN"
echo "Email: $EMAIL"
echo "======================================"

docker exec certbot certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d $DOMAIN \
  --email $EMAIL \
  --agree-tos \
  --no-eff-email \
  --force-renewal

echo ""
echo "Recargando Nginx..."
docker exec contenedor_nginx nginx -s reload

echo "¡Certificados generados exitosamente!"
