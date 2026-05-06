# Guía de Despliegue en AWS con Docker, Nginx y Certbot

## 1. Preparación en el servidor (Debian)

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clonar o subir el proyecto
git clone <tu-repositorio>
cd proyecto_final_DAW2
```

## 2. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar con tus valores
nano .env
```

**Importante:** Cambiar en `.env`:
- `SECRET_KEY`: Generar una nueva clave secreta
- `POSTGRES_PASSWORD`: Cambiar contraseña
- `DEBUG`: Mantener en `False`
- `DOMAIN`: Tu dominio (cafit.freemyip.com)
- `EMAIL_CERT`: Tu email para certificados SSL

## 3. Inicializar Certbot

```bash
cd www
chmod +x init-certbot.sh certbot-renew.sh entrypoint.sh
./init-certbot.sh
```

## 4. Levantar contenedores

```bash
docker-compose up -d
```

## 5. Generar certificados SSL reales

```bash
./certbot-renew.sh cafit.freemyip.com tu-email@example.com
```

## 6. Verificar estado

```bash
docker-compose ps
docker-compose logs -f web
docker-compose logs -f nginx
```

## Comandos útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Ejecutar migraciones manualmente
docker exec <nombre-web-container> python manage.py migrate

# Crear superusuario
docker exec -it <nombre-web-container> python manage.py createsuperuser

# Ver base de datos
docker exec -it postgres_db psql -U usuario_db -d nombre_db

# Recargar Nginx
docker exec contenedor_nginx nginx -s reload

# Renovar certificados manualmente
docker exec certbot certbot renew --webroot -w /var/www/certbot
```

## Solución de problemas

### Certificados no se generan
```bash
# Ver logs de certbot
docker logs certbot

# Verificar que Nginx está corriendo
docker logs contenedor_nginx
```

### Archivo estático no aparecen
```bash
# Recolectar archivos estáticos
docker exec <web-container> python manage.py collectstatic --noinput

# Recargar Nginx
docker exec contenedor_nginx nginx -s reload
```

### Conexión a base de datos rechazada
```bash
# Verificar que PostgreSQL está listo
docker logs postgres_db

# Ver si el contenedor web puede acceder a db
docker exec <web-container> python manage.py dbshell
```

### ERROR: CSRF verification failed
Asegúrate en `.env` que `ALLOWED_HOSTS` contiene tu dominio y que en `settings.py` está configurado correctamente.

## Actualizar código en producción

```bash
git pull origin main
docker-compose down
docker-compose up -d --build
```

## Backup de base de datos

```bash
docker exec postgres_db pg_dump -U usuario_db nombre_db > backup.sql
```

## Restore de base de datos

```bash
cat backup.sql | docker exec -i postgres_db psql -U usuario_db -d nombre_db
```
