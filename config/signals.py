from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from config.models import Perfil


@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crear un Perfil cuando se crea un nuevo Usuario.
    """
    if created:
        Perfil.objects.create(usuario=instance)


@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    """
    Guardar el Perfil cuando se actualiza el Usuario.
    """
    instance.perfil.save()
