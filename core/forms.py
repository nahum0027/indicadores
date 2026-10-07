from django import forms
from django.conf import settings

from .models import ReporteAdministracion, ReporteJuridico, ReporteOperaciones


class ReporteForm(forms.ModelForm):
    secciones = []

    class Meta:
        exclude = ("semana", "capturado_por", "tarde")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        nuevo = not self.instance.pk and not self.is_bound
        for nombre, campo in self.fields.items():
            campo.required = True
            campo.widget.attrs.update({"min": 0, "inputmode": "decimal", "class": "num", "placeholder": "0"})
            if nuevo:  # captura nueva: campos vacíos para no guardar ceros por descuido
                self.initial[nombre] = None

    def secciones_render(self):
        return [(titulo, ayuda, [self[c] for c in campos]) for titulo, ayuda, campos in self.secciones]


class OperacionesForm(ReporteForm):
    secciones = [
        ("Unidades", "", ["unidades_disponibles", "unidades_plan"]),
        ("Combustible", "Total de lunes a viernes.", ["litros"]),
        ("Personal de apoyo en rutas", "Personal de apoyo que se subió a rutas en la semana.", ["sup_rutas", "coord_rutas", "aux_rutas"]),
        ("Call Center", "", ["cc_recibidas", "cc_atendidas", "cc_quejas"]),
        ("Principales motivos de queja", "Cuántas de las quejas registradas fueron por cada motivo. El resto se cuenta como \"otros\".",
         ["q_parada", "q_frecuencia", "q_imprudente"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteOperaciones

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        meta = getattr(settings, "INDICADORES_PLAN_OPERATIVO", 335)
        self.fields["unidades_plan"].help_text = (
            f"Promedio diario de unidades que salieron a ruta de lunes a viernes (ej. 328.4). "
            f"El plan operativo es de {meta} unidades.")

    def clean(self):
        datos = super().clean()
        motivos = sum(datos.get(c) or 0 for c in ("q_parada", "q_frecuencia", "q_imprudente"))
        total = datos.get("cc_quejas") or 0
        if motivos > total:
            self.add_error("cc_quejas", f"La suma de los motivos ({motivos}) no puede ser mayor que el total de quejas.")
        if (datos.get("cc_atendidas") or 0) > (datos.get("cc_recibidas") or 0):
            self.add_error("cc_atendidas", "No puede haber más llamadas atendidas que recibidas.")
        return datos


class AdministracionForm(ReporteForm):
    secciones = [
        ("Personal", "Personas en plantilla al cierre de la semana.", ["plantilla_hombres", "plantilla_mujeres"]),
        ("Altas y bajas", "", ["altas", "bajas_renuncia", "bajas_despido", "bajas_abandono", "bajas_defuncion", "bajas_otro"]),
        ("Incapacidades", "Número de incapacidades iniciadas en la semana.",
         ["incap_enfermedad", "incap_riesgo", "incap_maternidad"]),
        ("Vacantes", "Vacantes abiertas al cierre.", ["vac_ejecutivo", "vac_administrativo", "vac_honorarios"]),
        ("Vacaciones", "Personas que tomaron vacaciones en la semana.", ["vaca_adm_h", "vaca_adm_m", "vaca_ops_h", "vaca_ops_m"]),
        ("Capacitación", "", ["cap_en_curso", "cap_liberados"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteAdministracion


class JuridicoForm(ReporteForm):
    secciones = [
        ("Audiencias", "Audiencias atendidas de lunes a domingo, por instancia.", ["aud_ccl", "aud_tca", "aud_juzgados"]),
        ("Siniestros", "Siniestros de lunes a domingo, según la responsabilidad de la empresa.",
         ["sin_responsable", "sin_no_responsable"]),
        ("Personas lesionadas por código", "Personas lesionadas en los siniestros de la semana.",
         ["les_verde", "les_amarillo", "les_rojo", "les_negro"]),
        ("Pólizas", "", ["polizas_activadas"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteJuridico
