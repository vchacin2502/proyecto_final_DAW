# Importaciones necesarias para vistas y decoradores
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
# ---existing code---

from .forms import AlimentoForm
from django.shortcuts import get_object_or_404

@login_required
@require_POST
def eliminar_usuario(request, id):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("admin_usuarios")
    try:
        user = User.objects.get(id=id)
        if user.is_superuser:
            messages.error(request, "No puedes eliminar un superusuario.")
        elif user == request.user:
            messages.error(request, "No puedes eliminar tu propio usuario.")
        else:
            user.delete()
            messages.success(request, "Usuario eliminado correctamente.")
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado.")
    return redirect("admin_usuarios")

@login_required
def editar_alimento(request, id):
    alimento = get_object_or_404(Alimento, id=id, usuario=request.user)
    if request.method == "POST":
        form = AlimentoForm(request.POST, instance=alimento)
        if form.is_valid():
            form.save()
            messages.success(request, "Alimento actualizado correctamente.")
            return redirect("alimentos")
    else:
        form = AlimentoForm(instance=alimento)
    return render(request, "paginas/alimento_form.html", {"form": form, "alimento": alimento})

from django.http import JsonResponse, Http404
# Vista para devolver los datos de un alimento en JSON
from .models import Alimento

def alimentos_detalle(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    try:
        alimento = Alimento.objects.get(id=id, usuario=request.user)
    except Alimento.DoesNotExist:
        raise Http404()
    data = {
        'id': alimento.id,
        'nombre': alimento.nombre,
        'marca': alimento.marca,
        'unidad': alimento.unidad,
        'cantidad_referencia': alimento.cantidad_referencia,
        'kcal': alimento.kcal,
        'proteinas': alimento.proteinas,
        'carbohidratos': alimento.carbohidratos,
        'azucares': alimento.azucares,
        'grasas': alimento.grasas,
        'saturadas': alimento.saturadas,
    }
    return JsonResponse(data)

# --- INTEGRATED FROM decorators.py ---
from django.core.exceptions import PermissionDenied

def staff_required(view_func):
    """Permite solo a usuarios staff (admin)."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied("No tienes permisos de administrador.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def superuser_required(view_func):
    """Permite solo a superusuarios."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied("No tienes permisos de superusuario.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
# --- END decorators.py ---

# --- INTEGRATED FROM utils.py ---
def mostrar_errores_formulario(request, errores):
    from django.contrib import messages
    for error in errores:
        messages.error(request, error)

def validar_texto_formulario(valor, etiqueta, requerido=True):
    texto = (valor or "").strip()
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return "", None
    return texto, None

def validar_entero_formulario(valor, etiqueta, requerido=True):
    texto = (valor or "").strip()
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return None, None
    try:
        numero = int(texto)
    except (TypeError, ValueError):
        return None, f"{etiqueta} debe ser un número entero."
    return numero, None

def validar_float_formulario(valor, etiqueta, requerido=True):
    texto = (valor or "").strip().replace(",", ".")
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return None, None
    try:
        numero = float(texto)
    except (TypeError, ValueError):
        return None, f"{etiqueta} debe ser un número válido."
    return numero, None

def validar_opcion_formulario(valor, etiqueta, opciones):
    if valor in opciones:
        return valor, None
    return None, f"{etiqueta} no es válida."

def a_flotante(value):
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return 0.0

def a_flotante_o_none(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
# --- END utils.py ---

import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.timezone import localtime, now
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_POST

from config.models import Alimento, Comida, ComidaAlimento, Incidencia, MensajeChat, Perfil, SalaChat


TIPOS_COMIDA = [
    ("desayuno", "Desayuno"),
    ("almuerzo", "Almuerzo"),
    ("cena", "Cena"),
    ("snacks", "Snacks"),
]

MESES_EN_ESPANOL = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]

CHAT_ROOMS = {
    "general": {
        "slug": "general",
        "name": "General",
        "description": "Conversaciones abiertas de la comunidad y novedades del dia.",
        "placeholder": "Escribe una actualizacion general para la comunidad...",
        "messages": [
            {"author": "Laura", "time": "09:12", "text": "Buenos dias, hoy empiezo una semana nueva de objetivos."},
            {"author": "Carlos", "time": "09:15", "text": "Mucho animo, yo tambien estoy retomando rutina."},
            {"author": "Marta", "time": "09:19", "text": "Recordad hidrataros bien, en mi caso me cambia el dia."},
        ],
    },
    "recetas": {
        "slug": "recetas",
        "name": "Recetas",
        "description": "Comparte ideas, preparaciones saludables y tips de cocina.",
        "placeholder": "Comparte una receta o un tip de cocina saludable...",
        "messages": [
            {"author": "Sergio", "time": "10:01", "text": "Tortitas de avena: 1 huevo, 40g avena y canela."},
            {"author": "Paula", "time": "10:04", "text": "Yo les pongo yogur natural y fruta por encima."},
            {"author": "Andrea", "time": "10:09", "text": "Gran idea, la pruebo hoy para merendar."},
        ],
    },
    "progreso": {
        "slug": "progreso",
        "name": "Progreso y motivacion",
        "description": "Cuenta tus avances semanales y motiva a otros usuarios.",
        "placeholder": "Comparte tu progreso de hoy y anima al resto...",
        "messages": [
            {"author": "David", "time": "08:45", "text": "Primer mes completado, he mejorado mucho en constancia."},
            {"author": "Noelia", "time": "08:52", "text": "Eso es clave, el progreso real viene de la disciplina."},
            {"author": "Juan", "time": "08:58", "text": "Vamos equipo, semana nueva y objetivos claros."},
        ],
    },
    "dudas": {
        "slug": "dudas",
        "name": "Dudas nutricionales",
        "description": "Preguntas sobre macros, alimentos y organizacion de comidas.",
        "placeholder": "Escribe tu duda nutricional para la comunidad...",
        "messages": [
            {"author": "Claudia", "time": "11:10", "text": "Si entreno tarde, como distribuyo mejor los carbohidratos?"},
            {"author": "Alberto", "time": "11:16", "text": "A mi me funciona meter una parte antes y otra despues."},
            {"author": "Eva", "time": "11:22", "text": "Depende del objetivo, pero esa estrategia suele ir bien."},
        ],
    },
}

CHAT_SALA_DEFINICION = [
    CHAT_ROOMS["general"],
    CHAT_ROOMS["recetas"],
    CHAT_ROOMS["progreso"],
    CHAT_ROOMS["dudas"],
]

def _mostrar_errores_formulario(request, errores):
    for error in errores:
        messages.error(request, error)


def _validar_texto_formulario(valor, etiqueta, *, requerido=True):
    texto = (valor or "").strip()
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return "", None
    return texto, None


def _validar_entero_formulario(valor, etiqueta, *, requerido=True):
    texto = (valor or "").strip()
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return None, None
    try:
        numero = int(texto)
    except (TypeError, ValueError):
        return None, f"{etiqueta} debe ser un numero entero."
    return numero, None


def _validar_float_formulario(valor, etiqueta, *, requerido=True):
    texto = (valor or "").strip().replace(",", ".")
    if not texto:
        if requerido:
            return None, f"{etiqueta} es obligatorio."
        return None, None
    try:
        numero = float(texto)
    except (TypeError, ValueError):
        return None, f"{etiqueta} debe ser un numero valido."
    return numero, None


def _validar_opcion_formulario(valor, etiqueta, opciones):
    if valor in opciones:
        return valor, None
    return None, f"{etiqueta} no es valida."



def clean_old_messages():
    """Borra automáticamente mensajes más antiguos de 24 horas."""
    cutoff_time = now() - timedelta(hours=24)
    deleted_count, _ = MensajeChat.objects.filter(creado_en__lt=cutoff_time).delete()
    return deleted_count


def _a_flotante(value):
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _a_flotante_o_none(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip().replace(",", ".")
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _calcular_calorias(datos_perfil):
    edad = _a_flotante(datos_perfil.get("edad"))
    altura = _a_flotante(datos_perfil.get("altura"))
    peso = _a_flotante(datos_perfil.get("peso"))
    sexo = datos_perfil.get("sexo", "Hombre")
    objetivo = datos_perfil.get("objetivo", "Mantener peso")

    if not edad or not altura or not peso:
        return 0

    if sexo == "Mujer":
        basal = 10 * peso + 6.25 * altura - 5 * edad - 161
    elif sexo == "Prefiero no decirlo":
        basal = 10 * peso + 6.25 * altura - 5 * edad - 78
    else:
        basal = 10 * peso + 6.25 * altura - 5 * edad + 5

    mantenimiento = basal * 1.4
    ajustes = {
        "Perder grasa": -400,
        "Mantener peso": 0,
        "Ganar masa muscular": 300,
    }
    return max(round(mantenimiento + ajustes.get(objetivo, 0)), 1200)


def _calcular_macros_objetivo(calorias, objetivo):
    if not calorias:
        return {"meta_proteinas": 0, "meta_grasas": 0, "meta_carbohidratos": 0}

    splits = {
        "Perder grasa": {"proteinas": 0.35, "grasas": 0.30, "carbohidratos": 0.35},
        "Mantener peso": {"proteinas": 0.30, "grasas": 0.30, "carbohidratos": 0.40},
        "Ganar masa muscular": {"proteinas": 0.30, "grasas": 0.25, "carbohidratos": 0.45},
    }
    ratio = splits.get(objetivo, splits["Mantener peso"])

    return {
        "meta_proteinas": round((calorias * ratio["proteinas"]) / 4),
        "meta_grasas": round((calorias * ratio["grasas"]) / 9),
        "meta_carbohidratos": round((calorias * ratio["carbohidratos"]) / 4),
    }


def inicio(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("acceso")


def _obtener_url_segura_siguiente(request):
    url_siguiente = request.POST.get("next") or request.GET.get("next")
    if url_siguiente and url_has_allowed_host_and_scheme(url_siguiente, {request.get_host()}):
        return url_siguiente
    return ""



def acceso(request):
    url_siguiente = _obtener_url_segura_siguiente(request)
    if request.user.is_authenticated:
        return redirect(url_siguiente or "dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        errores = []

        if not username:
            errores.append("El usuario es obligatorio.")

        if not password:
            errores.append("La contrasena es obligatoria.")

        if errores:
            _mostrar_errores_formulario(request, errores)
            return render(request, "paginas/acceso.html", {"next_url": url_siguiente, "auth_page": True})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(url_siguiente or "dashboard")
        messages.error(request, "Usuario o contrasena incorrectos.")

    return render(request, "paginas/acceso.html", {"next_url": url_siguiente, "auth_page": True})


def registro(request):
    url_siguiente = _obtener_url_segura_siguiente(request)
    if request.user.is_authenticated:
        return redirect(url_siguiente or "dashboard")

    if request.method == "POST":
        modelo_usuario = get_user_model()
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        errores = []

        if not username:
            errores.append("El usuario es obligatorio.")

        if not password:
            errores.append("La contrasena es obligatoria.")

        if errores:
            _mostrar_errores_formulario(request, errores)
            return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})

        if modelo_usuario.objects.filter(username__iexact=username).exists():
            messages.error(request, "Ese usuario ya existe. Elige otro.")
            return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})

        user = modelo_usuario.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect("completar_perfil")

    return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})


def _sexo_a_valor_bd(valor_ui):
    mapa = {"Hombre": "hombre", "Mujer": "mujer", "Prefiero no decirlo": "otro"}
    return mapa.get(valor_ui, "hombre")


def _sexo_a_valor_ui(valor_bd):
    mapa = {"hombre": "Hombre", "mujer": "Mujer", "otro": "Prefiero no decirlo"}
    return mapa.get(valor_bd, "Hombre")


def _objetivo_a_valor_bd(valor_ui):
    mapa = {
        "Perder grasa": "perder_grasa",
        "Mantener peso": "mantener_peso",
        "Ganar masa muscular": "ganar_musculo",
    }
    return mapa.get(valor_ui, "mantener_peso")


def _objetivo_a_valor_ui(valor_bd):
    mapa = {
        "perder_grasa": "Perder grasa",
        "mantener_peso": "Mantener peso",
        "ganar_musculo": "Ganar masa muscular",
    }
    return mapa.get(valor_bd, "Mantener peso")


def _obtener_perfil_usuario(usuario):
    perfil, _ = Perfil.objects.get_or_create(
        usuario=usuario,
        defaults={
            "sexo": "hombre",
            "objetivo": "mantener_peso",
        },
    )
    return perfil


def _perfil_a_contexto(perfil):
    return {
        "edad": perfil.edad or "",
        "altura": perfil.altura or "",
        "peso": perfil.peso or "",
        "sexo": _sexo_a_valor_ui(perfil.sexo),
        "objetivo": _objetivo_a_valor_ui(perfil.objetivo),
        "meta_calorias": perfil.meta_calorias or 0,
        "meta_proteinas": perfil.meta_proteinas or 0,
        "meta_grasas": perfil.meta_grasas or 0,
        "meta_carbohidratos": perfil.meta_carbohidratos or 0,
    }


def _obtener_datos_perfil(request):
    perfil = _obtener_perfil_usuario(request.user)
    datos_perfil = _perfil_a_contexto(perfil)
    if not datos_perfil["meta_calorias"]:
        datos_perfil["meta_calorias"] = _calcular_calorias(datos_perfil)
        datos_perfil.update(_calcular_macros_objetivo(datos_perfil["meta_calorias"], datos_perfil["objetivo"]))
    return datos_perfil


def _asegurar_salas_chat():
    salas = []
    for definicion in CHAT_SALA_DEFINICION:
        sala, _ = SalaChat.objects.get_or_create(
            slug=definicion["slug"],
            defaults={"nombre": definicion["name"]},
        )
        if sala.nombre != definicion["name"]:
            sala.nombre = definicion["name"]
            # sala.descripcion = definicion["description"]
            sala.save(update_fields=["nombre"])
        salas.append(sala)
    return salas


def _obtener_sala_chat(slug_sala):
    for sala in _asegurar_salas_chat():
        if sala.slug == slug_sala:
            return sala
    return None


def _guardar_perfil_desde_post(request):
    perfil = _obtener_perfil_usuario(request.user)
    errores = []
    advertencias = []

    edad_raw = request.POST.get("edad", "").strip()
    altura_raw = request.POST.get("altura", "").strip()
    peso_raw = request.POST.get("peso", "").strip()
    sexo_raw = request.POST.get("sexo", "Hombre")
    objetivo_raw = request.POST.get("objetivo", "Mantener peso")

    edad = int(edad_raw) if edad_raw else None
    if edad_raw and edad is None:
        errores.append("La edad debe ser un numero entero.")

    altura = _a_flotante_o_none(altura_raw)
    if altura_raw and altura is None:
        advertencias.append("La altura no tiene un formato valido. Se mantiene el valor anterior.")
        altura = perfil.altura

    peso = _a_flotante_o_none(peso_raw)
    if peso_raw and peso is None:
        advertencias.append("El peso no tiene un formato valido. Se mantiene el valor anterior.")
        peso = perfil.peso

    sexo = sexo_raw if sexo_raw in dict(Perfil.SEXO_CHOICES) else perfil.sexo
    if sexo_raw and sexo_raw not in dict(Perfil.SEXO_CHOICES):
        errores.append("El sexo no es valido.")

    objetivo = objetivo_raw if objetivo_raw in dict(Perfil.OBJETIVO_CHOICES) else perfil.objetivo
    if objetivo_raw and objetivo_raw not in dict(Perfil.OBJETIVO_CHOICES):
        errores.append("El objetivo no es valido.")

    if errores:
        _mostrar_errores_formulario(request, advertencias + errores)
        return False

    datos_perfil = {
        "edad": edad,
        "altura": altura,
        "peso": peso,
        "sexo": _sexo_a_valor_ui(sexo),
        "objetivo": _objetivo_a_valor_ui(objetivo),
        "meta_calorias": 0,
        "meta_proteinas": 0,
        "meta_grasas": 0,
        "meta_carbohidratos": 0,
    }
    datos_perfil["meta_calorias"] = _calcular_calorias(datos_perfil)
    datos_perfil.update(_calcular_macros_objetivo(datos_perfil["meta_calorias"], datos_perfil["objetivo"]))

    perfil.edad = edad
    perfil.altura = altura
    perfil.peso = peso
    perfil.sexo = sexo
    perfil.objetivo = objetivo
    perfil.meta_calorias = int(datos_perfil["meta_calorias"] or 0)
    perfil.meta_proteinas = int(datos_perfil["meta_proteinas"] or 0)
    perfil.meta_grasas = int(datos_perfil["meta_grasas"] or 0)
    perfil.meta_carbohidratos = int(datos_perfil["meta_carbohidratos"] or 0)
    perfil.save()
    return True


@login_required
def completar_perfil(request):
    datos_perfil = _obtener_datos_perfil(request)

    if request.method == "POST":
        if _guardar_perfil_desde_post(request):
            return redirect("dashboard")
        datos_perfil = _obtener_datos_perfil(request)

    return render(
        request,
        "paginas/completar_perfil.html",
        {"datos_perfil": datos_perfil, "auth_page": True, "auth_max_width": "980px"},
    )


@login_required
def chat(request):
    salas = _asegurar_salas_chat()
    return render(request, "paginas/chat.html", {"salas": salas})


@login_required
def chat_sala(request, sala_slug):
    clean_old_messages()
    
    sala = _obtener_sala_chat(sala_slug)
    if not sala:
        return redirect("chat")

    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion == "enviar_mensaje":
            contenido, error = _validar_texto_formulario(
                request.POST.get("contenido", ""),
                "El mensaje",
            )
            if error:
                messages.error(request, error)
            elif contenido:
                MensajeChat.objects.create(sala=sala, usuario=request.user, contenido=contenido)
            else:
                messages.error(request, "Escribe un mensaje antes de enviarlo.")
        elif accion == "reportar_mensaje":
            mensaje_id, error_id = _validar_entero_formulario(request.POST.get("mensaje_id", ""), "El mensaje reportado")
            razon, error_razon = _validar_texto_formulario(
                request.POST.get("razon", "Mensaje reportado desde la sala."),
                "La razon del reporte",
            )
            if error_id:
                messages.error(request, error_id)
            elif error_razon:
                messages.error(request, error_razon)
            else:
                mensaje = MensajeChat.objects.filter(id=mensaje_id, sala=sala).first()
                if mensaje:
                    Incidencia.objects.create(mensaje=mensaje, reportero=request.user, razon=razon)
                    messages.success(request, "Mensaje reportado para revision.")
                else:
                    messages.error(request, "No se pudo reportar ese mensaje.")
        elif accion == "borrar_mensaje":
            mensaje_id, error_id = _validar_entero_formulario(request.POST.get("mensaje_id", ""), "El mensaje")
            if error_id:
                messages.error(request, error_id)
            else:
                mensaje = MensajeChat.objects.filter(id=mensaje_id, sala=sala, usuario=request.user).first()
                if mensaje:
                    mensaje.delete()
                    messages.success(request, "Mensaje borrado.")
                else:
                    messages.error(request, "No puedes borrar ese mensaje.")
        return redirect("chat_sala", sala_slug=sala.slug)

    mensajes = MensajeChat.objects.filter(
        sala=sala,
        esta_oculto=False,
        estado_moderacion="visible",
    ).select_related("usuario").order_by("creado_en")
    salas = _asegurar_salas_chat()
    resumen_sala = next((definicion for definicion in CHAT_SALA_DEFINICION if definicion["slug"] == sala.slug), None)
    return render(
        request,
        "paginas/chat_sala.html",
        {
            "sala": sala,
            "salas": salas,
            "mensajes": mensajes,
            "resumen_sala": resumen_sala,
        },
    )


@login_required
@require_GET
def chat_mensajes_nuevos(request, sala_slug):
    sala = _obtener_sala_chat(sala_slug)
    if not sala:
        return JsonResponse({"detail": "Sala no encontrada."}, status=404)

    last_id_raw = request.GET.get("last_id", "0")
    try:
        last_id = int(last_id_raw)
    except (TypeError, ValueError):
        last_id = 0

    mensajes = (
        MensajeChat.objects.filter(
            sala=sala,
            id__gt=last_id,
            esta_oculto=False,
            estado_moderacion="visible",
        )
        .select_related("usuario")
        .order_by("creado_en", "id")
    )

    payload = []
    for mensaje in mensajes:
        es_propio = mensaje.usuario_id == request.user.id
        payload.append(
            {
                "id": mensaje.id,
                "usuario": mensaje.usuario.username if mensaje.usuario else "Anonimo",
                "contenido": mensaje.contenido,
                "creado_en": localtime(mensaje.creado_en).strftime("%H:%M"),
                "es_propio": es_propio,
                "puede_borrar": es_propio,
                "puede_reportar": not es_propio,
            }
        )

    return JsonResponse({"mensajes": payload})


@login_required
def perfil(request):
    datos_perfil = _obtener_datos_perfil(request)

    if request.method == "POST":
        if _guardar_perfil_desde_post(request):
            return redirect("perfil")
        datos_perfil = _obtener_datos_perfil(request)

    return render(request, "paginas/perfil.html", {"datos_perfil": datos_perfil})


@login_required
def dashboard(request):
    datos_perfil = _obtener_datos_perfil(request)
    comidas_hoy_qs = Comida.objects.filter(usuario=request.user, fecha_comida=date.today()).prefetch_related("comida_alimentos")
    historial_comidas = []
    for comida in comidas_hoy_qs.order_by("-creado_en"):
        items = []
        for item in comida.comida_alimentos.all():
            items.append(
                {
                    "nombre": item.nombre_snapshot,
                    "marca": item.marca_snapshot,
                    "cantidad": item.cantidad,
                    "unidad": item.unidad,
                    "kcal": item.kcal,
                    "proteinas": item.proteinas,
                    "carbohidratos": item.carbohidratos,
                    "azucares": item.azucares,
                    "grasas": item.grasas,
                    "saturadas": item.saturadas,
                }
            )
        totales_comida = comida.calcular_totales()
        historial_comidas.append(
            {
                "tipo_comida": comida.tipo_comida,
                "etiqueta_comida": comida.get_tipo_comida_display(),
                "items": items,
                "fecha_comida": comida.fecha_comida.isoformat(),
                "creado_en": comida.creado_en.strftime("%H:%M"),
                "totales": {k: round(v, 2) for k, v in totales_comida.items()},
                "indice_historial": comida.id,
            }
        )
    today_key = date.today().isoformat()
    comidas_hoy = [comida for comida in historial_comidas if comida.get("fecha_comida") == today_key]
    totales = {"kcal": 0, "proteinas": 0, "carbohidratos": 0, "azucares": 0, "grasas": 0, "saturadas": 0}

    for comida in comidas_hoy:
        for item in comida.get("items", []):
            totales["kcal"] += item["kcal"]
            totales["proteinas"] += item["proteinas"]
            totales["carbohidratos"] += item["carbohidratos"]
            totales["azucares"] += item["azucares"]
            totales["grasas"] += item["grasas"]
            totales["saturadas"] += item["saturadas"]

    # Normalize float sums to avoid artifacts like 384.20000000000005.
    totales["kcal"] = round(totales["kcal"], 2)
    totales["proteinas"] = round(totales["proteinas"], 2)
    totales["carbohidratos"] = round(totales["carbohidratos"], 2)
    totales["azucares"] = round(totales["azucares"], 2)
    totales["grasas"] = round(totales["grasas"], 2)
    totales["saturadas"] = round(totales["saturadas"], 2)

    meta_proteinas = int(datos_perfil.get("meta_proteinas") or 0)
    meta_grasas = int(datos_perfil.get("meta_grasas") or 0)
    meta_carbohidratos = int(datos_perfil.get("meta_carbohidratos") or 0)

    proteinas_pct = int(min(round(totales["proteinas"] / meta_proteinas * 100, 0) if meta_proteinas else 0, 100))
    grasas_pct = int(min(round(totales["grasas"] / meta_grasas * 100, 0) if meta_grasas else 0, 100))
    carbohidratos_pct = int(min(round(totales["carbohidratos"] / meta_carbohidratos * 100, 0) if meta_carbohidratos else 0, 100))

    macros = {
        "proteinas": {
            "actual": round(totales["proteinas"], 1),
            "objetivo": meta_proteinas,
            "porcentaje": proteinas_pct,
            "tono": _tono_progreso(proteinas_pct),
        },
        "grasas": {
            "actual": round(totales["grasas"], 1),
            "objetivo": meta_grasas,
            "porcentaje": grasas_pct,
            "tono": _tono_progreso(grasas_pct),
        },
        "carbohidratos": {
            "actual": round(totales["carbohidratos"], 1),
            "objetivo": meta_carbohidratos,
            "porcentaje": carbohidratos_pct,
            "tono": _tono_progreso(carbohidratos_pct),
        },
    }

    calorias_objetivo = int(round(_a_flotante(datos_perfil.get("meta_calorias"))))
    calorias_consumidas = int(round(totales["kcal"]))
    calorias_restantes = max(calorias_objetivo - calorias_consumidas, 0)
    progreso_calorias = int(min(round(calorias_consumidas / calorias_objetivo * 100, 0) if calorias_objetivo else 0, 100))

    comidas_mostrar = [comida for comida in historial_comidas if comida.get("fecha_comida") == today_key]

    return render(
        request,
        "paginas/dashboard.html",
        {
            "historial_comidas": list(reversed(comidas_mostrar)),
            "totales": totales,
            "macros": macros,
            "datos_perfil": datos_perfil,
            "calorias_objetivo": calorias_objetivo,
            "calorias_consumidas": calorias_consumidas,
            "calorias_restantes": calorias_restantes,
            "progreso_calorias": progreso_calorias,
            "tono_calorias": _tono_progreso(progreso_calorias),
        },
    )


def _obtener_catalogo_alimentos_usuario(request):
    alimentos = Alimento.objects.filter(usuario=request.user).order_by("nombre")
    return [
        {
            "id": alimento.id,
            "nombre": alimento.nombre,
            "marca": alimento.marca,
            "unidad": alimento.unidad,
            "cantidad_referencia": alimento.cantidad_referencia,
            "kcal": alimento.kcal,
            "proteinas": alimento.proteinas,
            "carbohidratos": alimento.carbohidratos,
            "azucares": alimento.azucares,
            "grasas": alimento.grasas,
            "saturadas": alimento.saturadas,
        }
        for alimento in alimentos
    ]


def _valores_porcion(alimento, cantidad):
    base = alimento.get("cantidad_referencia", 100) or 100
    factor = cantidad / base
    return {
        "kcal": round(alimento["kcal"] * factor, 2),
        "proteinas": round(alimento["proteinas"] * factor, 2),
        "carbohidratos": round(alimento["carbohidratos"] * factor, 2),
        "azucares": round(alimento["azucares"] * factor, 2),
        "grasas": round(alimento["grasas"] * factor, 2),
        "saturadas": round(alimento["saturadas"] * factor, 2),
    }


def _reescalar_valores_item(item, cantidad_nueva, unidad_nueva):
    cantidad_anterior = _a_flotante(item.get("cantidad"))
    if cantidad_anterior <= 0:
        return {
            "nombre": item.get("nombre", ""),
            "marca": item.get("marca", ""),
            "cantidad": round(cantidad_nueva, 2),
            "unidad": unidad_nueva,
            "kcal": 0,
            "proteinas": 0,
            "carbohidratos": 0,
            "azucares": 0,
            "grasas": 0,
            "saturadas": 0,
        }

    factor = cantidad_nueva / cantidad_anterior
    return {
        "nombre": item.get("nombre", ""),
        "marca": item.get("marca", ""),
        "cantidad": round(cantidad_nueva, 2),
        "unidad": unidad_nueva,
        "kcal": round(_a_flotante(item.get("kcal")) * factor, 2),
        "proteinas": round(_a_flotante(item.get("proteinas")) * factor, 2),
        "carbohidratos": round(_a_flotante(item.get("carbohidratos")) * factor, 2),
        "azucares": round(_a_flotante(item.get("azucares")) * factor, 2),
        "grasas": round(_a_flotante(item.get("grasas")) * factor, 2),
        "saturadas": round(_a_flotante(item.get("saturadas")) * factor, 2),
    }


def _tono_progreso(porcentaje):
    if porcentaje <= 49:
        return "danger"
    if porcentaje <= 89:
        return "orange"
    return "warning"


def _estado_diario(porcentaje_promedio):
    if porcentaje_promedio <= 49:
        return {"label": "Malo", "tono": "danger"}
    if porcentaje_promedio <= 79:
        return {"label": "Regular", "tono": "orange"}
    return {"label": "Bien", "tono": "success"}


def _porcentaje_progreso_comida(valor_total, valor_objetivo):
    if not valor_objetivo:
        return 0
    return int(min(round(valor_total / valor_objetivo * 100, 0), 100))


def _parsear_valor_mes(valor_mes):
    try:
        texto_año, texto_mes = valor_mes.split("-", 1)
        año = int(texto_año)
        mes = int(texto_mes)
        if 1 <= mes <= 12:
            return año, mes
    except (ValueError, AttributeError):
        pass
    hoy = date.today()
    return hoy.year, hoy.month


def _parsear_valor_fecha(valor_fecha):
    try:
        return datetime.strptime(valor_fecha, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return date.today()


def _build_calendar_context(request, historial_comidas, datos_perfil):
    today = date.today()
    current_year, current_month = _parsear_valor_mes(request.GET.get("month"))
    selected_day = _parsear_valor_fecha(request.GET.get("day") or today.isoformat())

    comidas_por_fecha = defaultdict(list)
    for comida in historial_comidas:
        fecha_comida = comida.get("fecha_comida") or today.isoformat()
        if not fecha_comida:
            continue
        comidas_por_fecha[fecha_comida].append(comida)

    estadisticas_diarias = {}
    meta_calorias = int(round(_a_flotante(datos_perfil.get("meta_calorias"))))
    meta_proteinas = int(datos_perfil.get("meta_proteinas") or 0)
    meta_grasas = int(datos_perfil.get("meta_grasas") or 0)
    meta_carbohidratos = int(datos_perfil.get("meta_carbohidratos") or 0)

    for fecha_comida, comidas in comidas_por_fecha.items():
        totales = {"kcal": 0, "proteinas": 0, "grasas": 0, "carbohidratos": 0, "azucares": 0, "saturadas": 0}
        for comida in comidas:
            totales_comida = comida.get("totales") or {}
            totales["kcal"] += _a_flotante(totales_comida.get("kcal"))
            totales["proteinas"] += _a_flotante(totales_comida.get("proteinas"))
            totales["grasas"] += _a_flotante(totales_comida.get("grasas"))
            totales["carbohidratos"] += _a_flotante(totales_comida.get("carbohidratos"))
            totales["azucares"] += _a_flotante(totales_comida.get("azucares"))
            totales["saturadas"] += _a_flotante(totales_comida.get("saturadas"))

        kcal_pct = _porcentaje_progreso_comida(totales["kcal"], meta_calorias)
        proteinas_pct = _porcentaje_progreso_comida(totales["proteinas"], meta_proteinas)
        grasas_pct = _porcentaje_progreso_comida(totales["grasas"], meta_grasas)
        carbs_pct = _porcentaje_progreso_comida(totales["carbohidratos"], meta_carbohidratos)
        progreso_promedio = round((kcal_pct + proteinas_pct + grasas_pct + carbs_pct) / 4) if any([kcal_pct, proteinas_pct, grasas_pct, carbs_pct]) else 0

        estadisticas_diarias[fecha_comida] = {
            "fecha": fecha_comida,
            "comidas": comidas,
            "totales": {
                "kcal": round(totales["kcal"], 2),
                "proteinas": round(totales["proteinas"], 2),
                "grasas": round(totales["grasas"], 2),
                "carbohidratos": round(totales["carbohidratos"], 2),
                "azucares": round(totales["azucares"], 2),
                "saturadas": round(totales["saturadas"], 2),
            },
            "porcentajes": {
                "kcal": kcal_pct,
                "proteinas": proteinas_pct,
                "grasas": grasas_pct,
                "carbohidratos": carbs_pct,
            },
            "progreso_promedio": progreso_promedio,
            "estado": _estado_diario(progreso_promedio),
        }

    calendar_grid = []
    month_calendar = calendar.Calendar(firstweekday=0).monthdatescalendar(current_year, current_month)
    for week in month_calendar:
        week_cells = []
        for day in week:
            day_key = day.isoformat()
            day_data = estadisticas_diarias.get(day_key)
            week_cells.append(
                {
                    "dia": day.day,
                    "fecha": day_key,
                    "parametro_mes": f"{day.year}-{day.month:02d}",
                    "en_mes": day.month == current_month,
                    "es_hoy": day == today,
                    "es_seleccionado": day == selected_day,
                    "tiene_datos": bool(day_data),
                    "estado": day_data["estado"] if day_data else None,
                    "progreso_promedio": day_data["progreso_promedio"] if day_data else 0,
                }
            )
        calendar_grid.append(week_cells)

    clave_seleccionada = selected_day.isoformat()
    datos_seleccionados = estadisticas_diarias.get(clave_seleccionada)

    if current_month == 1:
        prev_month_date = date(current_year - 1, 12, 1)
    else:
        prev_month_date = date(current_year, current_month - 1, 1)

    if current_month == 12:
        next_month_date = date(current_year + 1, 1, 1)
    else:
        next_month_date = date(current_year, current_month + 1, 1)

    return {
        "calendar_grid": calendar_grid,
        "calendar_month_name": MESES_EN_ESPANOL[current_month - 1],
        "calendar_year": current_year,
        "calendar_prev_month": prev_month_date.strftime("%Y-%m"),
        "calendar_next_month": next_month_date.strftime("%Y-%m"),
        "calendar_prev_day": prev_month_date.isoformat(),
        "calendar_next_day": next_month_date.isoformat(),
        "dia_seleccionado": selected_day,
        "datos_seleccionados": datos_seleccionados,
        "seleccion_tiene_datos": bool(datos_seleccionados),
        "resumen_mes": {
            "dias_con_datos": len(estadisticas_diarias),
            "progreso_promedio": round(sum(item["progreso_promedio"] for item in estadisticas_diarias.values()) / len(estadisticas_diarias)) if estadisticas_diarias else 0,
            "estado": _estado_diario(round(sum(item["progreso_promedio"] for item in estadisticas_diarias.values()) / len(estadisticas_diarias))) if estadisticas_diarias else {"label": "Sin datos", "tono": "secondary"},
        },
    }


def _normalizar_tipo_comida(tipo_comida):
    lookup = dict(TIPOS_COMIDA)
    return tipo_comida if tipo_comida in lookup else "desayuno"


@login_required
def agregar_comida_inicio(request):
    if request.method == "POST":
        tipo_comida = _normalizar_tipo_comida(request.POST.get("tipo_comida", ""))
        request.session["tipo_comida_pendiente"] = tipo_comida
        return redirect("agregar_comida_detalle")

    return render(request, "paginas/comida_inicio.html", {"tipos_comida": TIPOS_COMIDA})


@login_required
def agregar_comida_detalle(request):
    tipo_comida = request.session.get("tipo_comida_pendiente")
    if not tipo_comida:
        return redirect("agregar_comida_inicio")

    catalogo = _obtener_catalogo_alimentos_usuario(request)
    etiqueta_comida = dict(TIPOS_COMIDA).get(tipo_comida, "Comida")

    if request.method == "POST":
        errores = []
        items = []
        for alimento in catalogo:
            if request.POST.get(f"use_food_{alimento['id']}"):
                cantidad_raw = request.POST.get(f"qty_food_{alimento['id']}", "").strip()
                unidad = request.POST.get(f"unit_food_{alimento['id']}", alimento["unidad"])
                if not cantidad_raw:
                    errores.append(f"Debes indicar una cantidad para {alimento['nombre']}.")
                    continue
                cantidad, error = _validar_float_formulario(
                    cantidad_raw,
                    f"La cantidad de {alimento['nombre']}",
                    requerido=True,
                )
                if error:
                    errores.append(error)
                    continue
                porcion = _valores_porcion(alimento, cantidad)
                items.append(
                    {
                        "nombre": alimento["nombre"],
                        "marca": alimento["marca"],
                        "cantidad": cantidad,
                        "unidad": unidad,
                        "alimento_id": alimento["id"],
                        **porcion,
                    }
                )

        custom_name, error = _validar_texto_formulario(
            request.POST.get("custom_name", ""),
            "El nombre del alimento personalizado",
            requerido=False,
        )
        if error:
            errores.append(error)

        custom_qty_raw = request.POST.get("custom_qty", "").strip()
        custom_unit, error = _validar_opcion_formulario(request.POST.get("custom_unit", "g"), "La unidad personalizada", dict(Alimento.UNIDADES))
        if error:
            errores.append(error)

        if custom_name and custom_qty_raw:
            custom_qty, error = _validar_float_formulario(custom_qty_raw, "La cantidad personalizada")
            if error:
                errores.append(error)
            else:
                custom_food, _ = Alimento.objects.get_or_create(
                    usuario=request.user,
                    nombre=custom_name,
                    defaults={
                        "marca": request.POST.get("custom_marca", ""),
                        "unidad": request.POST.get("custom_base_unit", custom_unit),
                        "cantidad_referencia": float(request.POST.get("custom_ref_qty", "100") or 100),
                        "kcal": float(request.POST.get("custom_kcal", "0") or 0),
                        "proteinas": float(request.POST.get("custom_proteinas", "0") or 0),
                        "carbohidratos": float(request.POST.get("custom_carbohidratos", "0") or 0),
                        "azucares": float(request.POST.get("custom_azucares", "0") or 0),
                        "grasas": float(request.POST.get("custom_grasas", "0") or 0),
                        "saturadas": float(request.POST.get("custom_saturadas", "0") or 0),
                    },
                )
                custom_food_dict = {
                    "id": custom_food.id,
                    "nombre": custom_food.nombre,
                    "marca": custom_food.marca,
                    "unidad": custom_food.unidad,
                    "cantidad_referencia": custom_food.cantidad_referencia,
                    "kcal": custom_food.kcal,
                    "proteinas": custom_food.proteinas,
                    "carbohidratos": custom_food.carbohidratos,
                    "azucares": custom_food.azucares,
                    "grasas": custom_food.grasas,
                    "saturadas": custom_food.saturadas,
                }
                portion = _valores_porcion(custom_food_dict, custom_qty)
                items.append(
                    {
                        "nombre": custom_food.nombre,
                        "marca": custom_food.marca,
                        "cantidad": custom_qty,
                        "unidad": custom_unit,
                        "alimento_id": custom_food.id,
                        **portion,
                    }
                )

        if errores:
            _mostrar_errores_formulario(request, errores)
            return render(
                request,
                "paginas/comida_detalle.html",
                {
                    "tipo_comida": tipo_comida,
                    "etiqueta_comida": etiqueta_comida,
                    "catalogo": catalogo,
                    "modo_edicion": False,
                },
            )

        if not items:
            messages.error(request, "Selecciona al menos un alimento valido.")
            return render(
                request,
                "paginas/comida_detalle.html",
                {
                    "tipo_comida": tipo_comida,
                    "etiqueta_comida": etiqueta_comida,
                    "catalogo": catalogo,
                    "modo_edicion": False,
                },
            )

        with transaction.atomic():
            comida = Comida.objects.create(usuario=request.user, tipo_comida=tipo_comida, fecha_comida=date.today())
            for item in items:
                ComidaAlimento.objects.create(
                    comida=comida,
                    alimento_id=item.get("alimento_id"),
                    nombre_snapshot=item["nombre"],
                    marca_snapshot=item.get("marca", ""),
                    cantidad=item["cantidad"],
                    unidad=item["unidad"],
                    kcal=item["kcal"],
                    proteinas=item["proteinas"],
                    carbohidratos=item["carbohidratos"],
                    azucares=item["azucares"],
                    grasas=item["grasas"],
                    saturadas=item["saturadas"],
                )
        request.session.pop("tipo_comida_pendiente", None)
        return redirect("dashboard")

    return render(
        request,
        "paginas/comida_detalle.html",
        {
            "tipo_comida": tipo_comida,
            "etiqueta_comida": etiqueta_comida,
            "catalogo": catalogo,
            "modo_edicion": False,
            "items_existentes": [],
        },
    )


@login_required
def editar_comida(request, indice_comida):
    try:
        comida_actual = Comida.objects.prefetch_related("comida_alimentos").get(id=indice_comida, usuario=request.user)
    except Comida.DoesNotExist:
        return redirect("dashboard")

    tipo_comida = comida_actual.tipo_comida
    etiqueta_comida = comida_actual.get_tipo_comida_display()
    catalogo = _obtener_catalogo_alimentos_usuario(request)
    items_existentes = [
        {
            "nombre": item.nombre_snapshot,
            "marca": item.marca_snapshot,
            "cantidad": item.cantidad,
            "unidad": item.unidad,
            "kcal": item.kcal,
            "proteinas": item.proteinas,
            "carbohidratos": item.carbohidratos,
            "azucares": item.azucares,
            "grasas": item.grasas,
            "saturadas": item.saturadas,
        }
        for item in comida_actual.comida_alimentos.all()
    ]

    if request.method == "POST":
        errores = []
        items = []

        for indx, item_existente in enumerate(items_existentes):
            if not request.POST.get(f"existing_keep_{indx}"):
                continue
            cantidad_raw = request.POST.get(f"existing_qty_{indx}", "").strip()
            unidad = request.POST.get(f"existing_unit_{indx}", item_existente.get("unidad", "g"))
            if not cantidad_raw:
                errores.append(f"Debes indicar una cantidad para {item_existente['nombre']}.")
                continue
            cantidad, error = _validar_float_formulario(
                cantidad_raw,
                f"La cantidad de {item_existente['nombre']}",
                requerido=True,
            )
            if error:
                errores.append(error)
                continue
            if cantidad <= 0:
                errores.append(f"La cantidad de {item_existente['nombre']} debe ser mayor que 0.")
                continue
            items.append(_reescalar_valores_item(item_existente, cantidad, unidad))

        for alimento in catalogo:
            if request.POST.get(f"use_food_{alimento['id']}"):
                cantidad_raw = request.POST.get(f"qty_food_{alimento['id']}", "").strip()
                unidad = request.POST.get(f"unit_food_{alimento['id']}", alimento["unidad"])
                if not cantidad_raw:
                    errores.append(f"Debes indicar una cantidad para {alimento['nombre']}.")
                    continue
                cantidad, error = _validar_float_formulario(
                    cantidad_raw,
                    f"La cantidad de {alimento['nombre']}",
                    requerido=True,
                )
                if error:
                    errores.append(error)
                    continue
                if cantidad <= 0:
                    errores.append(f"La cantidad de {alimento['nombre']} debe ser mayor que 0.")
                    continue
                porcion = _valores_porcion(alimento, cantidad)
                items.append(
                    {
                        "nombre": alimento["nombre"],
                        "marca": alimento["marca"],
                        "cantidad": cantidad,
                        "unidad": unidad,
                        "alimento_id": alimento["id"],
                        **porcion,
                    }
                )

        custom_name, error = _validar_texto_formulario(
            request.POST.get("custom_name", ""),
            "El nombre del alimento personalizado",
            requerido=False,
        )
        if error:
            errores.append(error)

        custom_qty_raw = request.POST.get("custom_qty", "").strip()
        custom_unit, error = _validar_opcion_formulario(request.POST.get("custom_unit", "g"), "La unidad personalizada", dict(Alimento.UNIDADES))
        if error:
            errores.append(error)

        if custom_name and custom_qty_raw:
            custom_qty, error = _validar_float_formulario(custom_qty_raw, "La cantidad personalizada")
            if error:
                errores.append(error)
            else:
                custom_food, _ = Alimento.objects.get_or_create(
                    usuario=request.user,
                    nombre=custom_name,
                    defaults={
                        "marca": request.POST.get("custom_marca", ""),
                        "unidad": request.POST.get("custom_base_unit", custom_unit),
                        "cantidad_referencia": float(request.POST.get("custom_ref_qty", "100") or 100),
                        "kcal": float(request.POST.get("custom_kcal", "0") or 0),
                        "proteinas": float(request.POST.get("custom_proteinas", "0") or 0),
                        "carbohidratos": float(request.POST.get("custom_carbohidratos", "0") or 0),
                        "azucares": float(request.POST.get("custom_azucares", "0") or 0),
                        "grasas": float(request.POST.get("custom_grasas", "0") or 0),
                        "saturadas": float(request.POST.get("custom_saturadas", "0") or 0),
                    },
                )
                custom_food_dict = {
                    "id": custom_food.id,
                    "nombre": custom_food.nombre,
                    "marca": custom_food.marca,
                    "unidad": custom_food.unidad,
                    "cantidad_referencia": custom_food.cantidad_referencia,
                    "kcal": custom_food.kcal,
                    "proteinas": custom_food.proteinas,
                    "carbohidratos": custom_food.carbohidratos,
                    "azucares": custom_food.azucares,
                    "grasas": custom_food.grasas,
                    "saturadas": custom_food.saturadas,
                }
                portion = _valores_porcion(custom_food_dict, custom_qty)
                items.append(
                    {
                        "nombre": custom_food.nombre,
                        "marca": custom_food.marca,
                        "cantidad": custom_qty,
                        "unidad": custom_unit,
                        "alimento_id": custom_food.id,
                        **portion,
                    }
                )

        if errores:
            _mostrar_errores_formulario(request, errores)
            return render(
                request,
                "paginas/comida_detalle.html",
                {
                    "tipo_comida": tipo_comida,
                    "etiqueta_comida": etiqueta_comida,
                    "catalogo": catalogo,
                    "modo_edicion": True,
                    "indice_comida": indice_comida,
                    "items_existentes": items_existentes,
                },
            )

        if not items:
            messages.error(request, "Selecciona al menos un alimento valido.")
            return render(
                request,
                "paginas/comida_detalle.html",
                {
                    "tipo_comida": tipo_comida,
                    "etiqueta_comida": etiqueta_comida,
                    "catalogo": catalogo,
                    "modo_edicion": True,
                    "indice_comida": indice_comida,
                    "items_existentes": items_existentes,
                },
            )

        with transaction.atomic():
            comida_actual.comida_alimentos.all().delete()
            for item in items:
                ComidaAlimento.objects.create(
                    comida=comida_actual,
                    alimento_id=item.get("alimento_id"),
                    nombre_snapshot=item["nombre"],
                    marca_snapshot=item.get("marca", ""),
                    cantidad=item["cantidad"],
                    unidad=item["unidad"],
                    kcal=item["kcal"],
                    proteinas=item["proteinas"],
                    carbohidratos=item["carbohidratos"],
                    azucares=item["azucares"],
                    grasas=item["grasas"],
                    saturadas=item["saturadas"],
                )
        return redirect("dashboard")

    return render(
        request,
        "paginas/comida_detalle.html",
        {
            "tipo_comida": tipo_comida,
            "etiqueta_comida": etiqueta_comida,
            "catalogo": catalogo,
            "modo_edicion": True,
            "indice_comida": indice_comida,
            "items_existentes": items_existentes,
        },
    )


@login_required
def borrar_comida(request, indice_comida):
    Comida.objects.filter(id=indice_comida, usuario=request.user).delete()
    return redirect("dashboard")


@login_required
def alimentos(request):
    if request.method == "POST":
        errores = []
        nombre, error = _validar_texto_formulario(request.POST.get("nombre", ""), "El nombre")
        if error:
            errores.append(error)

        marca, error = _validar_texto_formulario(
            request.POST.get("marca", ""),
            "La marca",
            requerido=False,
        )
        if error:
            errores.append(error)

        unidad, error = _validar_opcion_formulario(request.POST.get("unidad", "g"), "La unidad", dict(Alimento.UNIDADES))
        if error:
            errores.append(error)

        cantidad_referencia, error = _validar_float_formulario(
            request.POST.get("cantidad_ref", "100"),
            "La cantidad de referencia",
            requerido=True,
        )
        if error:
            errores.append(error)

        kcal_ref, error = _validar_float_formulario(request.POST.get("kcal_ref_form", ""), "Las calorias")
        if error:
            errores.append(error)
        proteinas_ref, error = _validar_float_formulario(request.POST.get("prot_ref_form", ""), "Las proteinas")
        if error:
            errores.append(error)
        carbohidratos_ref, error = _validar_float_formulario(request.POST.get("carb_ref_form", ""), "Los carbohidratos")
        if error:
            errores.append(error)
        grasas_ref, error = _validar_float_formulario(request.POST.get("gras_ref_form", ""), "Las grasas")
        if error:
            errores.append(error)
        azucares_ref, error = _validar_float_formulario(request.POST.get("azucar_ref_form", ""), "Los azucares", requerido=False)
        if error:
            errores.append(error)
        saturadas_ref, error = _validar_float_formulario(request.POST.get("gras_sat_ref_form", ""), "Las grasas saturadas", requerido=False)
        if error:
            errores.append(error)

        if errores:
            _mostrar_errores_formulario(request, errores)
        elif nombre:
            Alimento.objects.create(
                usuario=request.user,
                nombre=nombre,
                marca=marca,
                unidad=unidad,
                cantidad_referencia=cantidad_referencia,
                kcal=kcal_ref if kcal_ref is not None else 0,
                proteinas=proteinas_ref if proteinas_ref is not None else 0,
                carbohidratos=carbohidratos_ref if carbohidratos_ref is not None else 0,
                azucares=azucares_ref or 0,
                grasas=grasas_ref if grasas_ref is not None else 0,
                saturadas=saturadas_ref or 0,
            )
            messages.success(request, "Alimento guardado.")
            return redirect("alimentos")

    busqueda = request.GET.get("q", "").strip()
    alimentos_qs = Alimento.objects.filter(usuario=request.user)
    if busqueda:
        alimentos_qs = alimentos_qs.filter(Q(nombre__icontains=busqueda) | Q(marca__icontains=busqueda))

    return render(
        request,
        "paginas/alimentos.html",
        {
            "alimentos": alimentos_qs.order_by("nombre"),
            "busqueda": busqueda,
        },
    )


@login_required
def estadisticas(request):
    datos_perfil = _obtener_datos_perfil(request)
    historial_comidas = []
    comidas = Comida.objects.filter(usuario=request.user).prefetch_related("comida_alimentos").order_by("-fecha_comida", "-creado_en")
    for comida in comidas:
        items = []
        for item in comida.comida_alimentos.all():
            items.append(
                {
                    "nombre": item.nombre_snapshot,
                    "marca": item.marca_snapshot,
                    "cantidad": item.cantidad,
                    "unidad": item.unidad,
                    "kcal": item.kcal,
                    "proteinas": item.proteinas,
                    "carbohidratos": item.carbohidratos,
                    "azucares": item.azucares,
                    "grasas": item.grasas,
                    "saturadas": item.saturadas,
                }
            )
        totales = comida.calcular_totales()
        historial_comidas.append(
            {
                "tipo_comida": comida.tipo_comida,
                "etiqueta_comida": comida.get_tipo_comida_display(),
                "items": items,
                "fecha_comida": comida.fecha_comida.isoformat(),
                "creado_en": comida.creado_en.strftime("%H:%M"),
                "totales": {k: round(v, 2) for k, v in totales.items()},
                "indice_historial": comida.id,
            }
        )
    contexto_calendario = _build_calendar_context(request, historial_comidas, datos_perfil)

    return render(
        request,
        "paginas/estadisticas.html",
        {
            "datos_perfil": datos_perfil,
            **contexto_calendario,
        },
    )


@login_required
def panel_admin(request):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("dashboard")
    
    total_incidencias = Incidencia.objects.filter(estado="abierta", mensaje__isnull=True).count()
    mensajes_reportados = MensajeChat.objects.filter(incidencias__isnull=False).distinct().count()
    usuarios_activos = User.objects.count()
    
    return render(request, "paginas/panel_admin.html", {
        "total_incidencias": total_incidencias,
        "mensajes_reportados": mensajes_reportados,
        "usuarios_activos": usuarios_activos,
    })


@login_required
def admin_incidencias(request):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("dashboard")
    
    # Manejar cambio de estado
    if request.method == "POST":
        incidencia_id = request.POST.get("incidencia_id")
        nuevo_estado = request.POST.get("estado")
        accion = request.POST.get("accion", "actualizar")
        estados_validos = {estado for estado, _ in Incidencia.ESTADO_INCIDENCIA}
        
        try:
            incidencia_id = int(incidencia_id)
            incidencia = Incidencia.objects.get(id=incidencia_id)
            if accion == "eliminar" or nuevo_estado == "rechazada":
                incidencia.delete()
            elif nuevo_estado in estados_validos:
                incidencia.estado = nuevo_estado
                incidencia.admin = request.user
                incidencia.save()
            else:
                messages.error(request, "El estado seleccionado no es valido.")
        except Incidencia.DoesNotExist:
            messages.error(request, "No se encontro la incidencia seleccionada.")
        except (TypeError, ValueError):
            messages.error(request, "La incidencia seleccionada no es valida.")
        
        return redirect("admin_incidencias")
    
    # GET: Mostrar incidencias
    filtro_estado = request.GET.get("estado", "")
    incidencias = (
        Incidencia.objects.select_related("mensaje", "reportero", "admin")
        .filter(mensaje__isnull=True)
        .order_by("-creada_en")
    )
    
    if filtro_estado:
        incidencias = incidencias.filter(estado=filtro_estado)
    
    return render(request, "paginas/admin_incidencias.html", {
        "incidencias": incidencias,
        "filtro_estado": filtro_estado,
    })


@login_required
def admin_chat(request):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("dashboard")
    
    # Manejar eliminación de mensaje
    if request.method == "POST":
        mensaje_id = request.POST.get("mensaje_id")
        
        try:
            mensaje = MensajeChat.objects.get(id=int(mensaje_id))
            # Eliminamos primero los reportes asociados para descartar su razon.
            Incidencia.objects.filter(mensaje=mensaje).delete()
            mensaje.delete()
            return redirect("admin_chat")
        except MensajeChat.DoesNotExist:
            messages.error(request, "No se encontro el mensaje seleccionado.")
            return redirect("admin_chat")
        except (TypeError, ValueError):
            messages.error(request, "El mensaje seleccionado no es valido.")
            return redirect("admin_chat")
    
    # GET: Mostrar mensajes con incidencias
    sala_slug = request.GET.get("sala", "")
    
    # Traer mensajes que tienen incidencias asociadas
    incidencias = Incidencia.objects.select_related(
        "mensaje", "reportero", "mensaje__sala"
    ).filter(
        mensaje__isnull=False
    ).order_by("-creada_en").distinct()
    
    if sala_slug:
        incidencias = incidencias.filter(mensaje__sala__slug=sala_slug)
    
    salas = SalaChat.objects.all().order_by("nombre")
    
    return render(request, "paginas/admin_chat.html", {
        "incidencias": incidencias,
        "salas": salas,
        "sala_slug": sala_slug,
    })


@login_required
def admin_usuarios(request):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("dashboard")

    # GET: Mostrar usuarios
    busqueda = request.GET.get("q", "").strip()
    usuarios = User.objects.all().order_by("username")

    if busqueda:
        usuarios = usuarios.filter(Q(username__icontains=busqueda) | Q(email__icontains=busqueda))

    usuarios_info = []
    for user in usuarios:
        usuarios_info.append({
            "user": user,
        })

    return render(request, "paginas/admin_usuarios.html", {
        "usuarios_info": usuarios_info,
        "busqueda": busqueda,
    })


@login_required
@require_POST
def reportar_problema(request):
    asunto, error_asunto = _validar_texto_formulario(
        request.POST.get("asunto", ""),
        "El asunto",
    )
    referer = request.META.get("HTTP_REFERER", "")
    destino = "dashboard"
    if referer and url_has_allowed_host_and_scheme(referer, {request.get_host()}):
        destino = referer

    if error_asunto:
        messages.error(request, error_asunto)
        return redirect(destino)

    if not asunto:
        return redirect(destino)

    # Crear una incidencia sin mensaje asociado (es un problema/bug reportado)
    Incidencia.objects.create(
        reportero=request.user,
        razon=asunto,
        estado="abierta"
    )

    return redirect(destino)


@login_required
@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Sesion cerrada.")
    return redirect("acceso")
