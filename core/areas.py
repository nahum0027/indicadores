from .forms import AdministracionForm, JuridicoForm, OperacionesForm
from .models import ReporteAdministracion, ReporteJuridico, ReporteOperaciones

# slug -> configuración. El "grupo" es el nombre del grupo de Django que puede capturar.
AREAS = {
    "operaciones": {
        "titulo": "Operaciones", "nombre": "Dirección de Operaciones", "responsable": "Héctor Hernández Vázquez", "grupo": "Operaciones", "dias": 5,
        "modelo": ReporteOperaciones, "form": OperacionesForm,
    },
    "administracion": {
        "titulo": "Administración", "nombre": "Dirección de Administración", "responsable": "José Alberto Baeza Ponce", "grupo": "Administracion", "dias": 5,
        "modelo": ReporteAdministracion, "form": AdministracionForm,
    },
    "juridico": {
        "titulo": "Jurídica", "nombre": "Dirección Jurídica", "responsable": "Arturo Eduardo Pérez Cruz", "grupo": "Juridico", "dias": 7,  # Jurídica sí incluye sábado y domingo
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
