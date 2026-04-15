from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    SEXO_CHOICES = [
        ("hombre", "Hombre"),
        ("mujer", "Mujer"),
        ("otro", "Prefiero no decirlo"),
    ]
    
    OBJETIVO_CHOICES = [
        ("perder_grasa", "Perder grasa"),
        ("mantener_peso", "Mantener peso"),
        ("ganar_musculo", "Ganar masa muscular"),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name="perfil")
    edad = models.IntegerField(blank=True, null=True)
    altura = models.FloatField(blank=True, null=True, help_text="En cm")
    peso = models.FloatField(blank=True, null=True, help_text="En kg")
    sexo = models.CharField(max_length=20, choices=SEXO_CHOICES, default="hombre")
    objetivo = models.CharField(max_length=20, choices=OBJETIVO_CHOICES, default="mantener_peso")
    meta_calorias = models.IntegerField(blank=True, null=True)
    meta_proteinas = models.IntegerField(blank=True, null=True)
    meta_grasas = models.IntegerField(blank=True, null=True)
    meta_carbohidratos = models.IntegerField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Alimento(models.Model):
    UNIDADES = [
        ("g", "Gramos"),
        ("ml", "Mililitros"),
        ("unidad", "Unidad"),
        ("cucharada", "Cucharada"),
        ("taza", "Taza"),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="alimentos")
    nombre = models.CharField(max_length=200)
    marca = models.CharField(max_length=200, blank=True)
    unidad = models.CharField(max_length=20, choices=UNIDADES, default="g")
    cantidad_referencia = models.FloatField(default=100, help_text="Cantidad base para los macros")
    kcal = models.FloatField()
    proteinas = models.FloatField()
    carbohidratos = models.FloatField()
    azucares = models.FloatField(default=0)
    grasas = models.FloatField()
    saturadas = models.FloatField(default=0)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.nombre} ({self.usuario.username})"


class Comida(models.Model):
    TIPO_COMIDA = [
        ("desayuno", "Desayuno"),
        ("almuerzo", "Almuerzo"),
        ("cena", "Cena"),
        ("snacks", "Snacks"),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comidas")
    tipo_comida = models.CharField(max_length=20, choices=TIPO_COMIDA)
    fecha_comida = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha_comida", "-creado_en"]

    def __str__(self):
        return f"{self.get_tipo_comida_display()} - {self.fecha_comida} ({self.usuario.username})"

    def calcular_totales(self):
        items = self.comida_alimentos.all()
        totales = {
            "kcal": 0,
            "proteinas": 0,
            "carbohidratos": 0,
            "azucares": 0,
            "grasas": 0,
            "saturadas": 0,
        }
        for item in items:
            totales["kcal"] += item.kcal
            totales["proteinas"] += item.proteinas
            totales["carbohidratos"] += item.carbohidratos
            totales["azucares"] += item.azucares
            totales["grasas"] += item.grasas
            totales["saturadas"] += item.saturadas
        return totales


class ComidaAlimento(models.Model):
    comida = models.ForeignKey(Comida, on_delete=models.CASCADE, related_name="comida_alimentos")
    alimento = models.ForeignKey(Alimento, on_delete=models.SET_NULL, null=True)
    nombre_snapshot = models.CharField(max_length=200, help_text="Nombre del alimento al momento de registrar")
    marca_snapshot = models.CharField(max_length=200, blank=True)
    cantidad = models.FloatField()
    unidad = models.CharField(max_length=20)
    kcal = models.FloatField()
    proteinas = models.FloatField()
    carbohidratos = models.FloatField()
    azucares = models.FloatField()
    grasas = models.FloatField()
    saturadas = models.FloatField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_snapshot} ({self.cantidad}{self.unidad}) en {self.comida}"


class SalaChat(models.Model):
    nombre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class MensajeChat(models.Model):
    ESTADO_MODERACION = [
        ("visible", "Visible"),
        ("oculto", "Oculto"),
        ("pendiente_revision", "Pendiente de revisión"),
    ]
    
    sala = models.ForeignKey(SalaChat, on_delete=models.CASCADE, related_name="mensajes")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)
    esta_oculto = models.BooleanField(default=False)
    estado_moderacion = models.CharField(max_length=20, choices=ESTADO_MODERACION, default="visible")

    class Meta:
        ordering = ["creado_en"]

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Anónimo'}: {self.contenido[:50]}"


class Incidencia(models.Model):
    ESTADO_INCIDENCIA = [
        ("abierta", "Abierta"),
        ("en_revision", "En revisión"),
        ("resuelta", "Resuelta"),
        ("rechazada", "Rechazada"),
    ]
    
    mensaje = models.ForeignKey(
        MensajeChat,
        on_delete=models.CASCADE,
        related_name="incidencias",
        null=True,
        blank=True,
    )
    reportero = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="incidencias_creadas")
    razon = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_INCIDENCIA, default="abierta")
    creada_en = models.DateTimeField(auto_now_add=True)
    # nota_admin eliminado: ya no se usa
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidencias_atendidas")

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"Incidencia {self.id} - {self.get_estado_display()}"
