def a_flotante_o_none(valor):
    try:
        if isinstance(valor, str):
            valor = valor.replace(",", ".")
        return float(valor)
    except (ValueError, TypeError):
        return None
def _build_calendar_context(request, historial_comidas, datos_perfil):
    today = date.today()
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))
    day_param = request.GET.get("day", str(today.day))
    try:
        if "-" in day_param:
            selected_day = int(day_param.split("-")[-1])
        else:
            selected_day = int(day_param)
    except Exception:
        selected_day = today.day
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdatescalendar(year, month)
    comidas_por_fecha = {c["fecha_comida"][:10]: c for c in historial_comidas}
    calendar_grid = []
    for week in month_days:
        week_row = []
        for day in week:
            day_str = day.isoformat()
            en_mes = (day.month == month)
            es_hoy = (day == today)
            es_seleccionado = (en_mes and day.day == selected_day)
            tiene_datos = day_str in comidas_por_fecha
            week_row.append({
                "dia": day.day,
                "fecha": day_str,
                "en_mes": en_mes,
                "es_hoy": es_hoy,
                "es_seleccionado": es_seleccionado,
                "tiene_datos": tiene_datos,
                "parametro_mes": month,
            })
        calendar_grid.append(week_row)
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    # Buscar todas las comidas del día seleccionado
    seleccion_tiene_datos = False
    comidas_dia = []
    for c in historial_comidas:
        if c["fecha_comida"][:10] == f"{year:04d}-{month:02d}-{selected_day:02d}":
            comidas_dia.append(c)
    if comidas_dia:
        seleccion_tiene_datos = True
        # datos_seleccionados: resumen del día + lista de comidas
        # Sumar totales del día
        totales = {"kcal": 0, "proteinas": 0, "carbohidratos": 0, "azucares": 0, "grasas": 0, "saturadas": 0}
        for comida in comidas_dia:
            for item in comida.get("items", []):
                totales["kcal"] += item["kcal"]
                totales["proteinas"] += item["proteinas"]
                totales["carbohidratos"] += item["carbohidratos"]
                totales["azucares"] += item["azucares"]
                totales["grasas"] += item["grasas"]
                totales["saturadas"] += item["saturadas"]
        for k in totales:
            totales[k] = round(totales[k], 2)
        datos_seleccionados = {
            "totales": totales,
            "comidas": comidas_dia,
        }
    else:
        datos_seleccionados = None

    return {
        "calendar_grid": calendar_grid,
        "calendar_month_name": MESES_EN_ESPANOL[month-1],
        "calendar_year": year,
        "calendar_prev_month": prev_month,
        "calendar_prev_day": 1,
        "calendar_next_month": next_month,
        "calendar_next_day": 1,
        "seleccion_tiene_datos": seleccion_tiene_datos,
        "datos_seleccionados": datos_seleccionados,
    }

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .models import Alimento

@login_required
@require_POST
def eliminar_alimento(request, id):
    alimento = get_object_or_404(Alimento, id=id, usuario=request.user)
    alimento.delete()
    messages.success(request, "Alimento eliminado correctamente.")
    return redirect("alimentos")

from .forms import AlimentoForm
from django.shortcuts import get_object_or_404

@login_required
@require_POST
def eliminar_usuario(request, id):
    if not request.user.is_staff:
        messages.warning(request, "No tienes permisos de administrador.")
        return redirect("admin_usuarios")
    user = get_object_or_404(User, id=id)
    if user.is_superuser:
        messages.error(request, "No puedes eliminar un superusuario.")
    elif user == request.user:
        messages.error(request, "No puedes eliminar tu propio usuario.")
    else:
        user.delete()
        messages.success(request, "Usuario eliminado correctamente.")
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
            messages.error(request, "Por favor, corrige los errores del formulario.")
    else:
        form = AlimentoForm(instance=alimento)
    return render(request, "paginas/alimento_form.html", {"form": form, "alimento": alimento})


from django.http import JsonResponse, Http404

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

def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.warning(request, "No tienes permisos de administrador.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper
def superuser_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.warning(request, "No tienes permisos de superusuario.")
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)
    return wrapper

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
    },
    "recetas": {
        "slug": "recetas",
        "name": "Recetas",
    },
    "progreso": {
        "slug": "progreso",
        "name": "Progreso y motivacion",
    },
    "dudas": {
        "slug": "dudas",
        "name": "Dudas nutricionales",
    },
}

CHAT_SALA_DEFINICION = [
    CHAT_ROOMS["general"],
    CHAT_ROOMS["recetas"],
    CHAT_ROOMS["progreso"],
    CHAT_ROOMS["dudas"],
]



def _calcular_calorias(datos_perfil):
    edad = a_flotante_o_none(datos_perfil.get("edad"))
    altura = a_flotante_o_none(datos_perfil.get("altura"))
    peso = a_flotante_o_none(datos_perfil.get("peso"))
    sexo = datos_perfil.get("sexo", "Hombre")
    objetivo = datos_perfil.get("objetivo", "Mantener peso")
    if objetivo == "bajar_peso":
        objetivo = "Bajar de peso"
    elif objetivo == "mantener_peso":
        objetivo = "Mantener peso"
    elif objetivo == "ganar_peso":
        objetivo = "Ganar peso"

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
        "Bajar de peso": -400,
        "Mantener peso": 0,
        "Ganar peso": 300,
    }
    return max(round(mantenimiento + ajustes.get(objetivo, 0)), 1200)


def _calcular_macros_objetivo(calorias, objetivo):
    if not calorias:
        return {"meta_proteinas": 0, "meta_grasas": 0, "meta_carbohidratos": 0}

    if objetivo == "bajar_peso":
        objetivo = "Bajar de peso"
    elif objetivo == "mantener_peso":
        objetivo = "Mantener peso"
    elif objetivo == "ganar_peso":
        objetivo = "Ganar peso"
    splits = {
        "Bajar de peso": {"proteinas": 0.35, "grasas": 0.30, "carbohidratos": 0.35},
        "Mantener peso": {"proteinas": 0.30, "grasas": 0.30, "carbohidratos": 0.40},
        "Ganar peso": {"proteinas": 0.30, "grasas": 0.25, "carbohidratos": 0.45},
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
            for error in errores:
                messages.error(request, error)
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
            for error in errores:
                messages.error(request, error)
            return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})

        if modelo_usuario.objects.filter(username__iexact=username).exists():
            messages.error(request, "Ese usuario ya existe. Elige otro.")
            return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})

        user = modelo_usuario.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect("completar_perfil")

    return render(request, "paginas/registro.html", {"next_url": url_siguiente, "auth_page": True})




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
        "sexo": perfil.sexo,
        "objetivo": perfil.objetivo,
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

    altura = a_flotante_o_none(altura_raw)
    if altura_raw and altura is None:
        advertencias.append("La altura no tiene un formato valido. Se mantiene el valor anterior.")
        altura = perfil.altura

    peso = a_flotante_o_none(peso_raw)
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
        for error in advertencias + errores:
            messages.error(request, error)
        return False

    datos_perfil = {
        "edad": edad,
        "altura": altura,
        "peso": peso,
        "sexo": sexo,
        "objetivo": objetivo,
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

    
    sala = _obtener_sala_chat(sala_slug)
    if not sala:
        return redirect("chat")

    if request.method == "POST":
        accion = request.POST.get("accion", "")
        if accion == "enviar_mensaje":
            contenido = request.POST.get("contenido", "")
            if not contenido.strip():
                error = "El mensaje no puede estar vacío."
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({"error": error}, status=400)
                messages.error(request, error)
            else:
                mensaje = MensajeChat.objects.create(sala=sala, usuario=request.user, contenido=contenido)
                if request.headers.get("x-requested-with") == "XMLHttpRequest":
                    return JsonResponse({
                        "mensaje": {
                            "id": mensaje.id,
                            "usuario": mensaje.usuario.username if mensaje.usuario else "Anonimo",
                            "contenido": mensaje.contenido,
                            "creado_en": localtime(mensaje.creado_en).strftime("%H:%M"),
                            "es_propio": True,
                            "puede_borrar": True,
                            "puede_reportar": False,
                        }
                    })
        elif accion == "reportar_mensaje":
            mensaje_id_raw = request.POST.get("mensaje_id", "")
            razon = request.POST.get("razon", "Mensaje reportado desde la sala.")
            try:
                mensaje_id = int(mensaje_id_raw)
            except (ValueError, TypeError):
                messages.error(request, "ID de mensaje no válido.")
                return redirect(request.path)
            if not razon or not razon.strip():
                messages.error(request, "La razón del reporte no puede estar vacía.")
                return redirect(request.path)
            try:
                mensaje = MensajeChat.objects.get(id=mensaje_id)
                from .models import Incidencia
                Incidencia.objects.create(
                    mensaje=mensaje,
                    reportero=request.user,
                    razon=razon.strip()
                )
                messages.success(request, "Mensaje reportado correctamente.")
            except MensajeChat.DoesNotExist:
                messages.error(request, "El mensaje no existe.")
                return redirect(request.path)
        elif accion == "borrar_mensaje":
            mensaje_id_raw = request.POST.get("mensaje_id", "")
            try:
                mensaje_id = int(mensaje_id_raw)
            except (ValueError, TypeError):
                messages.error(request, "ID de mensaje no válido.")
                return redirect(request.path)
            messages.success(request, "Mensaje borrado correctamente.")
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"ok": True})
        return redirect("chat_sala", sala_slug=sala.slug)

    mensajes = MensajeChat.objects.filter(
        sala=sala
    ).select_related("usuario").order_by("id")
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
        )
        .select_related("usuario")
        .order_by("id")
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
    for comida in comidas_hoy_qs.order_by("-fecha_comida"):
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
                # "creado_en" eliminado porque ya no existe
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
        },
        "grasas": {
            "actual": round(totales["grasas"], 1),
            "objetivo": meta_grasas,
            "porcentaje": grasas_pct,
        },
        "carbohidratos": {
            "actual": round(totales["carbohidratos"], 1),
            "objetivo": meta_carbohidratos,
            "porcentaje": carbohidratos_pct,
        },
    }

    calorias_objetivo = int(round(float(datos_perfil.get("meta_calorias", 0) or 0)))
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
    try:
        cantidad_anterior = float(item.get("cantidad", 0) or 0)
    except (ValueError, TypeError):
        cantidad_anterior = 0
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
    def safe_float(val):
        try:
            return float(val or 0)
        except (ValueError, TypeError):
            return 0

    return {
        "nombre": item.get("nombre", ""),
        "marca": item.get("marca", ""),
        "cantidad": round(cantidad_nueva, 2),
        "unidad": unidad_nueva,
        "kcal": round(safe_float(item.get("kcal")) * factor, 2),
        "proteinas": round(safe_float(item.get("proteinas")) * factor, 2),
        "carbohidratos": round(safe_float(item.get("carbohidratos")) * factor, 2),
        "azucares": round(safe_float(item.get("azucares")) * factor, 2),
        "grasas": round(safe_float(item.get("grasas")) * factor, 2),
        "saturadas": round(safe_float(item.get("saturadas")) * factor, 2),
    }

@login_required
def agregar_comida_inicio(request):

    if request.method == "POST":
        tipo_comida = request.POST.get("tipo_comida", "")
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
                try:
                    cantidad = float(cantidad_raw)
                    if cantidad <= 0:
                        errores.append(f"La cantidad de {alimento['nombre']} debe ser mayor que 0.")
                        continue
                except ValueError:
                    errores.append(f"La cantidad de {alimento['nombre']} debe ser un número válido.")
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

        custom_name = request.POST.get("custom_name", "")
        custom_qty_raw = request.POST.get("custom_qty", "").strip()
        custom_unit = request.POST.get("custom_unit", "g")
        if custom_name and custom_qty_raw:
            try:
                custom_qty = float(custom_qty_raw)
                if custom_qty <= 0:
                    errores.append("La cantidad personalizada debe ser mayor que 0.")
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
                    porcion = _valores_porcion(custom_food_dict, custom_qty)
                    items.append(
                        {
                            "nombre": custom_food.nombre,
                            "marca": custom_food.marca,
                            "cantidad": custom_qty,
                            "unidad": custom_unit,
                            "alimento_id": custom_food.id,
                            **porcion,
                        }
                    )
            except ValueError:
                errores.append("La cantidad personalizada debe ser un número válido.")

        if errores:
            for error in errores:
                messages.error(request, error)
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
            try:
                cantidad = float(cantidad_raw)
                if cantidad <= 0:
                    errores.append(f"La cantidad de {item_existente['nombre']} debe ser mayor que 0.")
                    continue
            except ValueError:
                errores.append(f"La cantidad de {item_existente['nombre']} debe ser un número válido.")
                continue
            items.append(_reescalar_valores_item(item_existente, cantidad, unidad))

        for alimento in catalogo:
            if request.POST.get(f"use_food_{alimento['id']}"):
                cantidad_raw = request.POST.get(f"qty_food_{alimento['id']}", "").strip()
                unidad = request.POST.get(f"unit_food_{alimento['id']}", alimento["unidad"])
                if not cantidad_raw:
                    errores.append(f"Debes indicar una cantidad para {alimento['nombre']}.")
                    continue
                try:
                    cantidad = float(cantidad_raw)
                    if cantidad <= 0:
                        errores.append(f"La cantidad de {alimento['nombre']} debe ser mayor que 0.")
                        continue
                except ValueError:
                    errores.append(f"La cantidad de {alimento['nombre']} no es válida.")
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

        custom_name = request.POST.get("custom_name", "")
        custom_qty_raw = request.POST.get("custom_qty", "").strip()
        custom_unit = request.POST.get("custom_unit", "g")
        if custom_name and custom_qty_raw:
            try:
                custom_qty = float(custom_qty_raw.replace(",", "."))
                if custom_qty <= 0:
                    errores.append("La cantidad personalizada debe ser mayor que 0.")
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
            except ValueError:
                errores.append("La cantidad personalizada debe ser un número válido.")

        if errores:
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
                    "errores": errores,
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
        nombre = request.POST.get("nombre", "")
        marca = request.POST.get("marca", "")
        unidad = request.POST.get("unidad", "g")
        cantidad_referencia = float(request.POST.get("cantidad_ref", "100") or 0)
        kcal_ref = float(request.POST.get("kcal_ref_form", "") or 0)
        proteinas_ref = float(request.POST.get("prot_ref_form", "") or 0)
        carbohidratos_ref = float(request.POST.get("carb_ref_form", "") or 0)
        grasas_ref = float(request.POST.get("gras_ref_form", "") or 0)
        azucares_ref = float(request.POST.get("azucar_ref_form", "") or 0)
        saturadas_ref = float(request.POST.get("gras_sat_ref_form", "") or 0)
        # Validaciones simples ya cubiertas arriba. Si hay errores, solo mostrar mensaje y redirigir.

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
    comidas = Comida.objects.filter(usuario=request.user).prefetch_related("comida_alimentos").order_by("-fecha_comida")
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
                # "creado_en" eliminado porque ya no existe
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
    
    total_incidencias = Incidencia.objects.filter(mensaje__isnull=True).count()
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
    
    # Manejar eliminación de incidencia
    if request.method == "POST":
        incidencia_id = request.POST.get("incidencia_id")
        accion = request.POST.get("accion", "actualizar")
        try:
            incidencia_id = int(incidencia_id)
            incidencia = Incidencia.objects.get(id=incidencia_id)
            if accion == "eliminar":
                incidencia.delete()
            else:
                messages.error(request, "Acción no válida.")
        except Incidencia.DoesNotExist:
            messages.error(request, "No se encontró la incidencia seleccionada.")
        except (TypeError, ValueError):
            messages.error(request, "La incidencia seleccionada no es válida.")
        return redirect("admin_incidencias")
    
    # GET: Mostrar incidencias
    incidencias = (
        Incidencia.objects.select_related("mensaje", "reportero")
        .filter(mensaje__isnull=True)
        .order_by("-id")
    )
    return render(request, "paginas/admin_incidencias.html", {
        "incidencias": incidencias,
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
    ).order_by("-id").distinct()
    
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
    asunto = request.POST.get("asunto", "").strip()
    referer = request.META.get("HTTP_REFERER", "")
    destino = "dashboard"
    if referer and url_has_allowed_host_and_scheme(referer, {request.get_host()}):
        destino = referer

    if not asunto:
        messages.error(request, "El asunto no puede estar vacío.")
        return redirect(destino)


    Incidencia.objects.create(
        reportero=request.user,
        razon=asunto
    )

    return redirect(destino)


@login_required
@require_POST
def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Sesion cerrada.")
    return redirect("acceso")
