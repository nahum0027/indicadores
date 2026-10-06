from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import Perfil, ReporteAdministracion, ReporteJuridico, ReporteOperaciones, UnidadesRuta


class RutaInline(admin.TabularInline):
    model = UnidadesRuta
    extra = 0


class BaseAdmin(admin.ModelAdmin):
    list_display = ("semana", "capturado_por", "entregado", "actualizado", "tarde")
    list_filter = ("tarde",)
    date_hierarchy = "semana"


@admin.register(ReporteOperaciones)
class OperacionesAdmin(BaseAdmin):
    inlines = [RutaInline]


admin.site.register(ReporteAdministracion, BaseAdmin)
admin.site.register(ReporteJuridico, BaseAdmin)
admin.site.site_header = "Indicadores CCPOTEQ"


class PerfilInline(admin.StackedInline):
    model = Perfil
    can_delete = False
    extra = 0


class UsuarioAdmin(UserAdmin):
    inlines = [PerfilInline]

    def get_inline_instances(self, request, obj=None):
        return super().get_inline_instances(request, obj) if obj else []  # al crear, el perfil lo hace la señal


User = get_user_model()
admin.site.unregister(User)
admin.site.register(User, UsuarioAdmin)
