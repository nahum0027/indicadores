from django.conf import settings
from django.db import models


def pct(a, b):
    return round(float(a) * 100 / float(b), 1) if b else None


def entero(nombre, ayuda=""):
    return models.PositiveIntegerField(nombre, default=0, help_text=ayuda)


class ReporteBase(models.Model):
    semana = models.DateField("Semana (lunes)", unique=True)
    capturado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    entregado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    tarde = models.BooleanField("Entregado tarde", default=False)

    class Meta:
        abstract = True
        ordering = ["-semana"]

    def __str__(self):
        return f"{self._meta.verbose_name} – {self.semana:%d/%m/%Y}"


class ReporteOperaciones(ReporteBase):
    unidades_disponibles = entero("Unidades disponibles", "Unidades en condiciones de salir a ruta")
    inhab_taller = entero("Inhabilitadas por taller", "Mantenimiento preventivo o correctivo")
    inhab_siniestro = entero("Inhabilitadas por siniestro")
    inhab_documentacion = entero("Inhabilitadas por documentación", "Permisos, verificación, placas, etc.")
    inhab_otro = entero("Inhabilitadas por otro motivo")
    corridas_programadas = entero("Corridas programadas", "Según el plan operativo de la semana")
    corridas_realizadas = entero("Corridas realizadas")
    litros = models.DecimalField("Litros de combustible", max_digits=12, decimal_places=2, default=0)
    costo_combustible = models.DecimalField("Costo de combustible ($)", max_digits=14, decimal_places=2, default=0)
    km_recorridos = models.DecimalField("Kilómetros recorridos", max_digits=12, decimal_places=2, default=0)

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte de Operaciones"
        verbose_name_plural = "reportes de Operaciones"

    @property
    def inhabilitadas(self):
        return self.inhab_taller + self.inhab_siniestro + self.inhab_documentacion + self.inhab_otro

    @property
    def flota_total(self):
        return self.unidades_disponibles + self.inhabilitadas

    @property
    def disponibilidad(self):
        return pct(self.unidades_disponibles, self.flota_total)

    @property
    def cumplimiento(self):
        return pct(self.corridas_realizadas, self.corridas_programadas)

    @property
    def rendimiento(self):
        return round(float(self.km_recorridos) / float(self.litros), 2) if self.litros else None

    @property
    def unidades_en_rutas(self):
        return sum(r.unidades for r in self.rutas.all())


class UnidadesRuta(models.Model):
    reporte = models.ForeignKey(ReporteOperaciones, on_delete=models.CASCADE, related_name="rutas")
    ruta = models.CharField("Ruta", max_length=60)
    unidades = models.PositiveIntegerField("Unidades", default=0)

    class Meta:
        ordering = ["ruta"]
        unique_together = [("reporte", "ruta")]
        verbose_name = "unidades por ruta"
        verbose_name_plural = "unidades por ruta"

    def __str__(self):
        return f"{self.ruta}: {self.unidades}"


class ReporteAdministracion(ReporteBase):
    plantilla_total = entero("Plantilla total al cierre", "Personas activas al domingo")
    altas = entero("Altas")
    bajas_renuncia = entero("Bajas por renuncia")
    bajas_despido = entero("Bajas por despido")
    bajas_abandono = entero("Bajas por abandono")
    bajas_otro = entero("Bajas por otro motivo")
    incap_enfermedad = entero("Incapacidades por enfermedad general")
    incap_riesgo = entero("Incapacidades por riesgo de trabajo")
    incap_maternidad = entero("Incapacidades por maternidad")
    dias_incapacidad = entero("Días de incapacidad acumulados", "Suma de días de todas las incapacidades de la semana")
    vac_operador = entero("Vacantes de operador")
    vac_mecanico = entero("Vacantes de mecánico")
    vac_administrativo = entero("Vacantes administrativas")
    vac_otro = entero("Otras vacantes")

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte de Administración"
        verbose_name_plural = "reportes de Administración"

    @property
    def bajas(self):
        return self.bajas_renuncia + self.bajas_despido + self.bajas_abandono + self.bajas_otro

    @property
    def incapacidades(self):
        return self.incap_enfermedad + self.incap_riesgo + self.incap_maternidad

    @property
    def vacantes(self):
        return self.vac_operador + self.vac_mecanico + self.vac_administrativo + self.vac_otro

    @property
    def rotacion(self):
        return pct(self.bajas, self.plantilla_total)


class ReporteJuridico(ReporteBase):
    aud_ccl = entero("Centro de Conciliación Laboral del Estado de Qro.")
    aud_tca = entero("Tribunal de Conciliación y Arbitraje del Estado de Qro.")
    aud_juzgados = entero("Juzgados Laborales del Estado de Qro.")
    siniestros = entero("Número de siniestros")
    resp_propia = entero("Responsabilidad de la empresa")
    resp_tercero = entero("Responsabilidad de terceros")
    resp_compartida = entero("Responsabilidad compartida")
    resp_proceso = entero("En determinación")
    les_verde = entero("Código verde")
    les_amarillo = entero("Código amarillo")
    les_rojo = entero("Código rojo")
    les_negro = entero("Código negro")
    polizas_activadas = entero("Activaciones de póliza")
    acuerdos_particulares = entero("Acuerdos entre particulares")

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte Jurídico"
        verbose_name_plural = "reportes Jurídicos"

    @property
    def audiencias(self):
        return self.aud_ccl + self.aud_tca + self.aud_juzgados

    @property
    def lesionados(self):
        return self.les_verde + self.les_amarillo + self.les_rojo + self.les_negro
