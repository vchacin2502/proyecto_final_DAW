#!/bin/bash

# Script para inicializar Certbot y generar certificados SSL

DOMAIN=${DOMAIN:-cafit.freemyip.com}
EMAIL=${EMAIL_CERT:-admin@example.com}
CERTBOT_DIR="./certbot"

echo "======================================"
echo "Inicializando Certbot para: $DOMAIN"
echo "Email: $EMAIL"
echo "======================================"

# Crear directorios si no existen
mkdir -p $CERTBOT_DIR/www
mkdir -p $CERTBOT_DIR/conf

# Generar certificados dummy iniciales para que Nginx pueda iniciar
echo "Generando certificados autofirmados temporales..."
mkdir -p $CERTBOT_DIR/conf/live/$DOMAIN

openssl req -x509 -newkey rsa:4096 -nodes \
  -out $CERTBOT_DIR/conf/live/$DOMAIN/fullchain.pem \
  -keyout $CERTBOT_DIR/conf/live/$DOMAIN/privkey.pem \
  -days 1 \
  -subj "/CN=$DOMAIN"

echo ""
echo "======================================"
echo "Iniciar los contenedores con:"
echo "docker-compose up -d"
echo ""
echo "Luego ejecutar la certificación real:"
echo "docker exec certbot certbot certonly --webroot -w /var/www/certbot -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email"
echo "======================================"
