from .forms import AdministracionForm, JuridicoForm, OperacionesForm
from .models import ReporteAdministracion, ReporteJuridico, ReporteOperaciones

# slug -> configuración. El "grupo" es el nombre del grupo de Django que puede capturar.
AREAS = {
    "operaciones": {
        "titulo": "Operaciones", "nombre": "Dirección de Operaciones", "grupo": "Operaciones",
        "modelo": ReporteOperaciones, "form": OperacionesForm,
    },
    "administracion": {
        "titulo": "Administración", "nombre": "Dirección de Administración", "grupo": "Administracion",
        "modelo": ReporteAdministracion, "form": AdministracionForm,
    },
    "juridico": {
        "titulo": "Jurídica", "nombre": "Dirección Jurídica", "grupo": "Juridico",
        "modelo": ReporteJuridico, "form": JuridicoForm,
    },
}
GRUPO_DIRECCION = "Direccion"


def areas_de_usuario(user):
    if not user.is_authenticated:
        return []
    if user.is_superuser:
        return list(AREAS)
    grupos = set(user.groups.values_list("name", flat=True))
    return [slug for slug, cfg in AREAS.items() if cfg["grupo"] in grupos]
