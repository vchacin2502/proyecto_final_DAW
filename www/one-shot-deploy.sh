#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/www/docker-compose.yml"
ENV_FILE="$PROJECT_ROOT/.env"

cd "$PROJECT_ROOT"

if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$PROJECT_ROOT/.env.example" ]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    echo "Se creo .env desde .env.example"
  else
    echo "ERROR: Falta .env y .env.example"
    exit 1
  fi
fi

# Normalize Windows CRLF in .env to avoid bash parse errors on Linux
sed -i 's/\r$//' "$ENV_FILE"

# 1) Levantar stack y certificado temporal
bash "$PROJECT_ROOT/www/deploy.sh"

# 2) Intentar certificado real (si falla, el sitio sigue levantado con temporal)
if timeout 180 bash "$PROJECT_ROOT/www/issue-cert.sh"; then
  echo "SSL real emitido correctamente"
else
  echo "Aviso: no se pudo emitir SSL real ahora"
  echo "Revisa DNS/puerto 80 y vuelve a ejecutar: bash www/issue-cert.sh"
fi

# 3) Mostrar estado final
sleep 2
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps

echo "Prueba local en la instancia:"
echo "curl -I http://localhost"
echo "curl -k -I https://localhost"
