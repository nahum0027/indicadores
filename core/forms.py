from django import forms

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
        ("Unidades activas e inactivas", "Estado de la flota en la semana.",
         ["unidades_disponibles", "inhab_taller", "inhab_siniestro", "inhab_documentacion", "inhab_otro"]),
        ("Plan operativo", "", ["corridas_programadas", "corridas_realizadas"]),
        ("Combustible", "Totales de lunes a viernes.", ["litros", "cargas", "consumo_promedio"]),
        ("Call Center", "", ["cc_recibidas", "cc_atendidas", "cc_quejas"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteOperaciones


class AdministracionForm(ReporteForm):
    secciones = [
        ("Plantilla", "", ["plantilla_total"]),
        ("Altas y bajas", "", ["altas", "bajas_renuncia", "bajas_despido", "bajas_abandono", "bajas_otro"]),
        ("Incapacidades", "Número de incapacidades iniciadas en la semana.",
         ["incap_enfermedad", "incap_riesgo", "incap_maternidad", "dias_incapacidad"]),
        ("Vacantes", "Vacantes abiertas al cierre.", ["vac_operador", "vac_mecanico", "vac_administrativo", "vac_otro"]),
        ("Vacaciones", "Personas que tomaron vacaciones en la semana.", ["vaca_adm_h", "vaca_adm_m", "vaca_ops_h", "vaca_ops_m"]),
        ("Capacitación", "", ["cap_en_curso", "cap_liberados", "cap_bajas"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteAdministracion


class JuridicoForm(ReporteForm):
    secciones = [
        ("Audiencias", "Audiencias atendidas en la semana, por instancia.", ["aud_ccl", "aud_tca", "aud_juzgados"]),
        ("Siniestros", "", ["siniestros"]),
        ("Determinación de responsabilidad", "Casos resueltos o en proceso durante la semana.",
         ["resp_propia", "resp_tercero", "resp_compartida", "resp_proceso"]),
        ("Personas lesionadas por código", "", ["les_verde", "les_amarillo", "les_rojo", "les_negro"]),
        ("Pólizas", "", ["polizas_activadas"]),
    ]

    class Meta(ReporteForm.Meta):
        model = ReporteJuridico
