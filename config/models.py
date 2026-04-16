from django.db import models
from django.contrib.auth.models import User


class Perfil(models.Model):
    SEXO_CHOICES = [
        ("hombre", "Hombre"),
        ("mujer", "Mujer"),
    ]
    OBJETIVO_CHOICES = [
        ("bajar_peso", "Bajar de peso"),
        ("mantener_peso", "Mantener peso"),
        ("ganar_peso", "Ganar peso"),
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

    def __str__(self):
        return f"Perfil de {self.usuario.username}"


class Alimento(models.Model):
    UNIDADES = [
        ("g", "Gramos"),
        ("ml", "Mililitros"),
        ("unidad", "Unidad"),
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

    class Meta:
        ordering = ["nombre"]

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

    class Meta:
        ordering = ["-fecha_comida"]

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
    sala = models.ForeignKey(SalaChat, on_delete=models.CASCADE, related_name="mensajes")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    contenido = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["creado_en"]

    def __str__(self):
        return f"{self.usuario.username if self.usuario else 'Anónimo'}: {self.contenido[:50]}"


class Incidencia(models.Model):
    mensaje = models.ForeignKey(
        MensajeChat,
        on_delete=models.CASCADE,
        related_name="incidencias",
        null=True,
        blank=True,
    )
    reportero = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="incidencias_creadas")
    razon = models.TextField()

    def __str__(self):
        return f"Incidencia {self.id} - {self.razon[:30]}"
