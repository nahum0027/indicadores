from django.shortcuts import redirect
from django.urls import reverse

from .models import Perfil


class CambioClaveObligatorioMiddleware:
    """Si el usuario tiene contraseña temporal, solo lo deja ir a cambiarla (o salir)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            perfil, _ = Perfil.objects.get_or_create(user=user)
            permitidas = (reverse("cambiar_clave"), reverse("logout"), "/static/")
            if perfil.debe_cambiar_clave and not request.path.startswith(permitidas):
                return redirect("cambiar_clave")
        return self.get_response(request)
