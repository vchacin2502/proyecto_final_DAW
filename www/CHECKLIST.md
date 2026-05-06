# Checklist de Despliegue en Producción

## Antes de desplegar:

- [ ] Generar nueva `SECRET_KEY` (no usar la de desarrollo)
- [ ] Cambiar `DEBUG = False` en settings.py (ya está configurado en `.env`)
- [ ] Cambiar todas las contraseñas en `.env`
- [ ] Configurar `ALLOWED_HOSTS` correcto
- [ ] Configurar `CSRF_TRUSTED_ORIGINS` para HTTPS
- [ ] Verificar DNS apunta a IP de AWS
- [ ] Tener certificado SSL válido antes de usar HTTPS

## En el servidor:

- [ ] Instalar Docker y Docker Compose
- [ ] Clonar repositorio
- [ ] Configurar `.env` con valores seguros
- [ ] Ejecutar `chmod +x www/*.sh`
- [ ] Ejecutar `./www/init-certbot.sh`
- [ ] Ejecutar `docker-compose up -d`
- [ ] Ejecutar `./www/certbot-renew.sh dominio email`
- [ ] Crear superusuario: `docker exec -it web python manage.py createsuperuser`
- [ ] Verificar que los archivos estáticos se cargaron
- [ ] Probar acceso en https://cafit.freemyip.com
- [ ] Configurar renovación automática de certificados

## Verificaciones de seguridad:

- [ ] `DEBUG = False`
- [ ] `SECRET_KEY` es secreta y aleatoria
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] Base de datos con contraseña fuerte
- [ ] Nginx redirige HTTP a HTTPS
- [ ] Certificados SSL válidos

## Monitoreo continuo:

- [ ] Ver logs regularmente: `docker-compose logs -f`
- [ ] Renovación de certificados automática (Certbot)
- [ ] Backups regulares de base de datos
- [ ] Actualizar dependencias de pip regularmente
