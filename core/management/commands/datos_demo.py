import random
from datetime import timedelta

from django.core.management.base import BaseCommand

from core.models import ReporteAdministracion, ReporteJuridico, ReporteOperaciones, UnidadesRuta
from core.periodos import periodo_actual

RUTAS = ["L01", "L02", "L05", "L08", "L12", "L15", "L21", "L33"]


class Command(BaseCommand):
    help = "Genera 12 semanas de datos de prueba (no usar en producción real)."

    def add_arguments(self, parser):
        parser.add_argument("--borrar", action="store_true", help="Borra todos los reportes antes")
        parser.add_argument("--sin-ultima", action="store_true", help="Deja sin capturar la semana actual")

    def handle(self, *args, **o):
        if o["borrar"]:
            for M in (ReporteOperaciones, ReporteAdministracion, ReporteJuridico):
                M.objects.all().delete()
        actual = periodo_actual()
        r = random.Random(7)
        inicio = 1 if o["sin_ultima"] else 0
        for i in range(inicio, 12):
            s = actual - timedelta(weeks=i)
            inhab = [r.randint(6, 14), r.randint(0, 4), r.randint(0, 3), r.randint(0, 2)]
            disp = 180 - sum(inhab)
            prog = r.randint(5200, 5400)
            km = r.randint(118000, 126000)
            litros = km / r.uniform(2.6, 3.0)
            op, _ = ReporteOperaciones.objects.update_or_create(semana=s, defaults=dict(
                unidades_disponibles=disp, inhab_taller=inhab[0], inhab_siniestro=inhab[1],
                inhab_documentacion=inhab[2], inhab_otro=inhab[3],
                corridas_programadas=prog, corridas_realizadas=int(prog * r.uniform(.9, .99)),
                litros=round(litros, 2), costo_combustible=round(litros * 25.4, 2), km_recorridos=km,
                tarde=(i == 3)))
            op.rutas.all().delete()
            restantes = disp
            for j, ruta in enumerate(RUTAS):
                n = restantes if j == len(RUTAS) - 1 else r.randint(14, 26)
                restantes -= n
                UnidadesRuta.objects.create(reporte=op, ruta=ruta, unidades=max(n, 0))
            ReporteAdministracion.objects.update_or_create(semana=s, defaults=dict(
                plantilla_total=r.randint(610, 630), altas=r.randint(2, 9), bajas_renuncia=r.randint(1, 6),
                bajas_despido=r.randint(0, 2), bajas_abandono=r.randint(0, 3), bajas_otro=r.randint(0, 1),
                incap_enfermedad=r.randint(3, 10), incap_riesgo=r.randint(0, 3), incap_maternidad=r.randint(0, 1),
                dias_incapacidad=r.randint(20, 70), vac_operador=r.randint(8, 18), vac_mecanico=r.randint(0, 3),
                vac_administrativo=r.randint(0, 2), vac_otro=r.randint(0, 2)))
            sin = r.randint(2, 9)
            ReporteJuridico.objects.update_or_create(semana=s, defaults=dict(
                aud_ccl=r.randint(1, 6), aud_tca=r.randint(0, 3), aud_juzgados=r.randint(0, 4), siniestros=sin,
                resp_propia=r.randint(0, sin // 2), resp_tercero=r.randint(0, sin // 2), resp_compartida=r.randint(0, 1),
                resp_proceso=r.randint(0, 2), les_verde=r.randint(0, 5), les_amarillo=r.randint(0, 2),
                les_rojo=r.randint(0, 1), les_negro=0, polizas_activadas=r.randint(0, sin),
                acuerdos_particulares=r.randint(0, 3)))
        self.stdout.write(self.style.SUCCESS(f"Datos demo listos ({12 - inicio} semanas)."))
