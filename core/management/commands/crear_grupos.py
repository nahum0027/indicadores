import os

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from core.areas import AREAS, GRUPO_DIRECCION


class Command(BaseCommand):
    help = "Crea los grupos por dirección y, si hay variables de entorno, el superusuario inicial."

    def handle(self, *args, **opts):
        for nombre in [c["grupo"] for c in AREAS.values()] + [GRUPO_DIRECCION]:
            _, creado = Group.objects.get_or_create(name=nombre)
            if creado:
                self.stdout.write(f"Grupo creado: {nombre}")

        usuario = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        clave = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        User = get_user_model()
        if usuario and clave and not User.objects.filter(username=usuario).exists():
            User.objects.create_superuser(usuario, os.environ.get("DJANGO_SUPERUSER_EMAIL", ""), clave)
            self.stdout.write(f"Superusuario creado: {usuario}")
