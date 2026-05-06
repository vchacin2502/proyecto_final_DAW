#!/bin/bash

# Script para generar una SECRET_KEY segura para Django

echo "Generando SECRET_KEY segura para Django..."
python3 -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())"

echo ""
echo "Copia el valor anterior al archivo .env"
