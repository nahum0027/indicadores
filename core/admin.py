from django.contrib import admin

from .models import ReporteAdministracion, ReporteJuridico, ReporteOperaciones, UnidadesRuta


class RutaInline(admin.TabularInline):
    model = UnidadesRuta
    extra = 0


class BaseAdmin(admin.ModelAdmin):
    list_display = ("semana", "capturado_por", "entregado", "tarde")
    list_filter = ("tarde",)
    date_hierarchy = "semana"


@admin.register(ReporteOperaciones)
class OperacionesAdmin(BaseAdmin):
    inlines = [RutaInline]


admin.site.register(ReporteAdministracion, BaseAdmin)
admin.site.register(ReporteJuridico, BaseAdmin)
admin.site.site_header = "Indicadores CCPOTEQ"
