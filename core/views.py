from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.utils import timezone

from .areas import AREAS, areas_de_usuario
from .models import ReporteOperaciones, UnidadesRuta
from .periodos import (etiqueta_corta, etiqueta_semana, fecha_larga, limite_de,
                       parse_semana, periodo_actual)

# ---------------------------------------------------------------- captura


def _formset_rutas(request, instancia, semana):
    inicial = []
    if instancia is None and request.method != "POST":
        previo = ReporteOperaciones.objects.filter(semana__lt=semana).order_by("-semana").first()
        if previo:  # precarga las rutas de la semana anterior
            inicial = [{"ruta": r.ruta, "unidades": r.unidades} for r in previo.rutas.all()]
    extra = max(len(inicial), 3) if instancia is None else 1
    FS = inlineformset_factory(ReporteOperaciones, UnidadesRuta, fields=("ruta", "unidades"),
                               extra=extra, can_delete=True)
    return FS(request.POST or None, instance=instancia or ReporteOperaciones(),
              initial=inicial or None, prefix="rutas")


@login_required
def capturar(request, area):
    if area not in AREAS:
        raise Http404
    if area not in areas_de_usuario(request.user):
        return HttpResponseForbidden("No tienes permiso para capturar esta área.")
    cfg = AREAS[area]
    Modelo = cfg["modelo"]

    semana = periodo_actual()
    if request.user.is_staff:  # staff puede corregir semanas anteriores con ?semana=AAAA-MM-DD
        semana = parse_semana(request.GET.get("semana")) or semana

    limite = limite_de(semana)
    vencido = timezone.now() > limite
    instancia = Modelo.objects.filter(semana=semana).first()
    bloqueado = vencido and settings.INDICADORES_BLOQUEAR_TARDE and not request.user.is_staff

    form = cfg["form"](request.POST or None, instance=instancia)
    formset = _formset_rutas(request, instancia, semana) if area == "operaciones" else None

    if request.method == "POST":
        if bloqueado:
            messages.error(request, "El plazo de esta semana ya cerró. Pide a un administrador que capture la corrección.")
            return redirect("capturar", area=area)
        if form.is_valid() and (formset is None or formset.is_valid()):
            obj = form.save(commit=False)
            obj.semana = semana
            obj.capturado_por = request.user
            if instancia is None:
                obj.tarde = vencido
            elif not request.user.is_staff:
                obj.tarde = obj.tarde or vencido
            obj.save()
            if formset is not None:
                formset.instance = obj
                formset.save()
            messages.success(request, f"{cfg['titulo']}: indicadores guardados para la {etiqueta_semana(semana).lower()}.")
            return redirect(f"/?semana={semana.isoformat()}#{area}")
        messages.error(request, "Revisa los campos marcados.")

    return render(request, "core/captura.html", {
        "area": area, "cfg": cfg, "form": form, "formset": formset,
        "semana": semana, "semana_txt": etiqueta_semana(semana),
        "limite_txt": fecha_larga(limite), "vencido": vencido,
        "bloqueado": bloqueado, "instancia": instancia,
    })


# ---------------------------------------------------------------- dashboard

FMT = {
    "int": (lambda v: f"{v:,.0f}", lambda d: f"{d:+,.0f}"),
    "pct": (lambda v: f"{v:.1f}%", lambda d: f"{d:+.1f} pts"),
    "money": (lambda v: f"${v / 1e6:,.2f} M" if abs(v) >= 1e6 else f"${v:,.0f}",
              lambda d: f"{'+' if d >= 0 else '−'}${abs(d):,.0f}"),
    "dec": (lambda v: f"{v:,.2f}", lambda d: f"{d:+,.2f}"),
}


def _kpi(titulo, actual, anterior, attr, fmt="int", sube_es_bueno=None, nota=""):
    val = getattr(actual, attr) if actual else None
    ant = getattr(anterior, attr) if anterior else None
    f_val, f_delta = FMT[fmt]
    k = {"titulo": titulo, "valor": f_val(float(val)) if val is not None else "—",
         "delta": None, "tono": "neutro", "nota": nota}
    if val is not None and ant is not None:
        d = float(val) - float(ant)
        k["delta"] = "sin cambio" if d == 0 else f_delta(d)
        if d and sube_es_bueno is not None:
            k["tono"] = "bien" if (d > 0) == sube_es_bueno else "mal"
        k["flecha"] = "▲" if d > 0 else "▼" if d < 0 else ""
    return k


def _serie(objs, attr):
    out = []
    for o in objs:
        v = getattr(o, attr) if o else None
        out.append(float(v) if v is not None else None)
    return out


def _actual(obj, attrs):
    return [getattr(obj, a) for a in attrs] if obj else None


@login_required
def dashboard(request):
    hoy = periodo_actual()
    semana = parse_semana(request.GET.get("semana")) or hoy
    if semana > hoy:
        semana = hoy
    semanas = [semana - timedelta(weeks=i) for i in range(11, -1, -1)]
    ant_semana = semana - timedelta(weeks=1)

    d = {}
    for slug, cfg in AREAS.items():
        qs = cfg["modelo"].objects.filter(semana__in=semanas)
        if slug == "operaciones":
            qs = qs.prefetch_related("rutas")
        por_semana = {r.semana: r for r in qs}
        d[slug] = {"serie": [por_semana.get(s) for s in semanas],
                   "actual": por_semana.get(semana), "anterior": por_semana.get(ant_semana)}

    # Entregas de la semana seleccionada
    limite = limite_de(semana)
    vencido = timezone.now() > limite
    entregas = []
    for slug, cfg in AREAS.items():
        r = d[slug]["actual"]
        if r:
            estado, txt = ("tarde", "Entregó tarde") if r.tarde else ("ok", "Entregado")
            detalle = fecha_larga(r.entregado)
        else:
            estado, txt = ("vencido", "Sin entregar") if vencido else ("pendiente", "Pendiente")
            detalle = ""
        entregas.append({"slug": slug, "nombre": cfg["nombre"], "responsable": cfg["responsable"], "estado": estado, "txt": txt, "detalle": detalle})

    restante = None
    if not vencido:
        seg = int((limite - timezone.now()).total_seconds())
        dias, seg = divmod(seg, 86400)
        horas, seg = divmod(seg, 3600)
        restante = (f"{dias} d " if dias else "") + f"{horas} h {seg // 60} min"

    op, op_prev, op_s = d["operaciones"]["actual"], d["operaciones"]["anterior"], d["operaciones"]["serie"]
    ad, ad_prev, ad_s = d["administracion"]["actual"], d["administracion"]["anterior"], d["administracion"]["serie"]
    ju, ju_prev, ju_s = d["juridico"]["actual"], d["juridico"]["anterior"], d["juridico"]["serie"]

    kpis = {
        "operaciones": [
            _kpi("Flota total", op, op_prev, "flota_total"),
            _kpi("Unidades activas", op, op_prev, "unidades_disponibles", sube_es_bueno=True),
            _kpi("Unidades inactivas", op, op_prev, "inhabilitadas", sube_es_bueno=False),
            _kpi("Flota activa", op, op_prev, "disponibilidad", "pct", True),
            _kpi("Cumplimiento del plan", op, op_prev, "cumplimiento", "pct", True),
            _kpi("Litros de combustible", op, op_prev, "litros", sube_es_bueno=False),
            _kpi("Cargas", op, op_prev, "cargas"),
            _kpi("Consumo promedio km/L", op, op_prev, "consumo_promedio", "dec", True),
            _kpi("Llamadas recibidas", op, op_prev, "cc_recibidas"),
            _kpi("% de llamadas atendidas", op, op_prev, "cc_atencion", "pct", True),
            _kpi("Quejas", op, op_prev, "cc_quejas", sube_es_bueno=False),
        ],
        "administracion": [
            _kpi("Plantilla", ad, ad_prev, "plantilla_total"),
            _kpi("Altas", ad, ad_prev, "altas"),
            _kpi("Bajas", ad, ad_prev, "bajas", sube_es_bueno=False),
            _kpi("Rotación semanal", ad, ad_prev, "rotacion", "pct", False),
            _kpi("Incapacidades", ad, ad_prev, "incapacidades", sube_es_bueno=False),
            _kpi("Días de incapacidad", ad, ad_prev, "dias_incapacidad", sube_es_bueno=False),
            _kpi("Vacantes abiertas", ad, ad_prev, "vacantes", sube_es_bueno=False),
            _kpi("Personal de vacaciones", ad, ad_prev, "vacaciones"),
            _kpi("En capacitación", ad, ad_prev, "cap_en_curso"),
            _kpi("Liberados de capacitación", ad, ad_prev, "cap_liberados", sube_es_bueno=True),
            _kpi("Bajas en capacitación", ad, ad_prev, "cap_bajas", sube_es_bueno=False),
        ],
        "juridico": [
            _kpi("Audiencias", ju, ju_prev, "audiencias"),
            _kpi("Siniestros", ju, ju_prev, "siniestros", sube_es_bueno=False),
            _kpi("Personas lesionadas", ju, ju_prev, "lesionados", sube_es_bueno=False),
            _kpi("Activaciones de póliza", ju, ju_prev, "polizas_activadas", sube_es_bueno=False),
        ],
    }

    graficas = {
        "labels": [etiqueta_corta(s) for s in semanas],
        "ops": {
            "disponibilidad": _serie(op_s, "disponibilidad"),
            "cumplimiento": _serie(op_s, "cumplimiento"),
            "disponibles": _serie(op_s, "unidades_disponibles"),
            "inhabilitadas": _serie(op_s, "inhabilitadas"),
            "litros": _serie(op_s, "litros"),
            "consumo": _serie(op_s, "consumo_promedio"),
            "cc_recibidas": _serie(op_s, "cc_recibidas"),
            "cc_atendidas": _serie(op_s, "cc_atendidas"),
            "cc_quejas": _serie(op_s, "cc_quejas"),
            "inhab_motivos": _actual(op, ["inhab_taller", "inhab_siniestro", "inhab_documentacion", "inhab_otro"]),
            "rutas": {"labels": [r.ruta for r in op.rutas.all()], "data": [r.unidades for r in op.rutas.all()]} if op else None,
        },
        "adm": {
            "altas": _serie(ad_s, "altas"),
            "bajas": _serie(ad_s, "bajas"),
            "rotacion": _serie(ad_s, "rotacion"),
            "incap_enf": _serie(ad_s, "incap_enfermedad"),
            "incap_riesgo": _serie(ad_s, "incap_riesgo"),
            "incap_mat": _serie(ad_s, "incap_maternidad"),
            "bajas_motivos": _actual(ad, ["bajas_renuncia", "bajas_despido", "bajas_abandono", "bajas_otro"]),
            "vacantes": _actual(ad, ["vac_operador", "vac_mecanico", "vac_administrativo", "vac_otro"]),
            "vacaciones": _actual(ad, ["vaca_adm_h", "vaca_adm_m", "vaca_ops_h", "vaca_ops_m"]),
            "cap_curso": _serie(ad_s, "cap_en_curso"),
            "cap_liberados": _serie(ad_s, "cap_liberados"),
            "cap_bajas": _serie(ad_s, "cap_bajas"),
        },
        "jur": {
            "ccl": _serie(ju_s, "aud_ccl"),
            "tca": _serie(ju_s, "aud_tca"),
            "juz": _serie(ju_s, "aud_juzgados"),
            "siniestros": _serie(ju_s, "siniestros"),
            "lesionados_serie": _serie(ju_s, "lesionados"),
            "polizas": _serie(ju_s, "polizas_activadas"),
            "resp": _actual(ju, ["resp_propia", "resp_tercero", "resp_compartida", "resp_proceso"]),
            "lesionados": _actual(ju, ["les_verde", "les_amarillo", "les_rojo", "les_negro"]),
        },
    }

    opciones = [hoy - timedelta(weeks=i) for i in range(0, 26)]
    return render(request, "core/dashboard.html", {
        "semana": semana, "semana_txt": etiqueta_semana(semana), "es_actual": semana == hoy,
        "anterior": (semana - timedelta(weeks=1)).isoformat(),
        "siguiente": (semana + timedelta(weeks=1)).isoformat() if semana < hoy else None,
        "opciones": [(s.isoformat(), etiqueta_semana(s)) for s in opciones],
        "limite_txt": fecha_larga(limite), "vencido": vencido, "restante": restante,
        "entregas": entregas, "entregados": sum(e["estado"] in ("ok", "tarde") for e in entregas),
        "kpis": kpis, "graficas": graficas,
        "areas": [(s, c["titulo"]) for s, c in AREAS.items()],
    })
