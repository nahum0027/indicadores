from .areas import AREAS, areas_de_usuario


def navegacion(request):
    return {"mis_areas": [(s, AREAS[s]["titulo"]) for s in areas_de_usuario(request.user)]}
