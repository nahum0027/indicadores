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
    unidades_plan = entero("Unidades en el plan operativo", "Unidades que salen según el plan operativo de la semana")
    litros = models.DecimalField("Litros de diésel", max_digits=12, decimal_places=2, default=0)
    sup_rutas = entero("Supervisores", "Supervisores que se subieron a rutas en la semana")
    coord_rutas = entero("Coordinadores", "Coordinadores que se subieron a rutas en la semana")
    aux_rutas = entero("Auxiliares", "Auxiliares que se subieron a rutas en la semana")
    cc_recibidas = entero("Llamadas recibidas")
    cc_atendidas = entero("Llamadas atendidas")
    cc_quejas = entero("Quejas registradas")

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte de Operaciones"
        verbose_name_plural = "reportes de Operaciones"

    @property
    def personal_rutas(self):
        return self.sup_rutas + self.coord_rutas + self.aux_rutas

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
    plantilla_hombres = entero("Hombres", "Hombres en plantilla al viernes")
    plantilla_mujeres = entero("Mujeres", "Mujeres en plantilla al viernes")
    altas = entero("Altas")
    bajas_renuncia = entero("Bajas por renuncia")
    bajas_despido = entero("Bajas por despido")
    bajas_abandono = entero("Bajas por abandono")
    bajas_otro = entero("Bajas por otro motivo")
    incap_enfermedad = entero("Incapacidades por enfermedad general")
    incap_riesgo = entero("Incapacidades por riesgo de trabajo")
    incap_maternidad = entero("Incapacidades por maternidad")
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
    def plantilla_total(self):
        return self.plantilla_hombres + self.plantilla_mujeres


class ReporteJuridico(ReporteBase):
    aud_ccl = entero("Centro de Conciliación Laboral del Estado de Qro.")
    aud_tca = entero("Tribunal de Conciliación y Arbitraje del Estado de Qro.")
    aud_juzgados = entero("Juzgados Laborales del Estado de Qro.")
    sin_responsable = entero("Responsable", "Siniestros en los que la empresa resultó responsable")
    sin_no_responsable = entero("No responsable", "Siniestros en los que la empresa no resultó responsable")
    les_verde = entero("Código verde", "Lesiones leves")
    les_amarillo = entero("Código amarillo", "Lesiones moderadas")
    les_rojo = entero("Código rojo", "Lesiones graves")
    les_negro = entero("Código negro", "Personas fallecidas")
    polizas_activadas = entero("Activaciones de póliza")

    class Meta(ReporteBase.Meta):
        verbose_name = "reporte Jurídico"
        verbose_name_plural = "reportes Jurídicos"

    @property
    def audiencias(self):
        return self.aud_ccl + self.aud_tca + self.aud_juzgados

    @property
    def siniestros(self):
        return self.sin_responsable + self.sin_no_responsable

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
