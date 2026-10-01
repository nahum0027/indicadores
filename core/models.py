from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    unidades_disponibles = entero("Unidades activas", "Unidades que salieron a ruta / en condiciones de operar")
    inhab_taller = entero("Inactivas por taller", "Mantenimiento preventivo o correctivo")
    inhab_siniestro = entero("Inactivas por siniestro")
    inhab_documentacion = entero("Inactivas por documentación", "Permisos, verificación, placas, etc.")
    inhab_otro = entero("Inactivas por otro motivo")
    corridas_programadas = entero("Corridas programadas", "Según el plan operativo de la semana")
    corridas_realizadas = entero("Corridas realizadas")
    litros = models.DecimalField("Litros", max_digits=12, decimal_places=2, default=0)
    cargas = entero("Cargas de combustible", "Número de cargas realizadas en la semana")
    consumo_promedio = models.DecimalField("Consumo promedio (km/L)", max_digits=6, decimal_places=2, default=0,
                                           help_text="Kilómetros por litro promedio de la flota")
    cc_recibidas = entero("Llamadas recibidas")
    cc_atendidas = entero("Llamadas atendidas")
    cc_quejas = entero("Quejas registradas")

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
    def litros_por_carga(self):
        return round(float(self.litros) / self.cargas, 1) if self.cargas else None

    @property
    def cc_atencion(self):
        return pct(self.cc_atendidas, self.cc_recibidas)


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
    plantilla_total = entero("Plantilla total al cierre", "Personas activas al viernes")
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
    vaca_adm_h = entero("Administración: hombres")
    vaca_adm_m = entero("Administración: mujeres")
    vaca_ops_h = entero("Operaciones: hombres")
    vaca_ops_m = entero("Operaciones: mujeres")
    cap_en_curso = entero("Personal en capacitación")
    cap_liberados = entero("Liberados")
    cap_bajas = entero("Bajas en capacitación")

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
    def vacaciones(self):
        return self.vaca_adm_h + self.vaca_adm_m + self.vaca_ops_h + self.vaca_ops_m

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

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte Jurídico"
        verbose_name_plural = "reportes Jurídicos"

    @property
    def audiencias(self):
        return self.aud_ccl + self.aud_tca + self.aud_juzgados

    @property
    def lesionados(self):
        return self.les_verde + self.les_amarillo + self.les_rojo + self.les_negro


class Perfil(models.Model):
    """Datos extra del usuario. Por ahora solo controla el cambio de contraseña obligatorio."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    debe_cambiar_clave = models.BooleanField(
        "Debe cambiar su contraseña al entrar", default=True,
        help_text="Márcalo cuando le asignes o restablezcas una contraseña temporal.",
    )

    class Meta:
        verbose_name = "perfil"
        verbose_name_plural = "perfil"

    def __str__(self):
        return f"Perfil de {self.user}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_perfil(sender, instance, created, **kwargs):
    if created:
        # Los usuarios nuevos entran con contraseña temporal; el superusuario inicial no.
        Perfil.objects.get_or_create(user=instance, defaults={"debe_cambiar_clave": not instance.is_superuser})
