"""Reglas de semanas: cada lunes (9:00 a 10:00) se carga lo generado de lunes a viernes de la semana anterior."""
from datetime import date, datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def lunes_de(d: date) -> date:
    return d - timedelta(days=d.weekday())


def periodo_actual(ahora=None) -> date:
    """Lunes de la semana que toca reportar ahora (la semana pasada)."""
    ahora = timezone.localtime(ahora or timezone.now())
    return lunes_de(ahora.date()) - timedelta(days=7)


def limite_de(semana: date) -> datetime:
    """El lunes siguiente a la semana reportada, a la hora límite."""
    entrega = semana + timedelta(days=7)
    return timezone.make_aware(
        datetime.combine(entrega, time(settings.INDICADORES_HORA_LIMITE)),
        timezone.get_current_timezone(),
    )


def parse_semana(texto):
    if not texto:
        return None
    try:
        return lunes_de(date.fromisoformat(texto))
    except ValueError:
        return None


def etiqueta_semana(s: date, dias: int = 5) -> str:
    """dias=5: lunes a viernes; dias=7: lunes a domingo (Jurídica)."""
    fin = s + timedelta(days=dias - 1)
    num = s.isocalendar()[1]
    if s.month == fin.month:
        rango = f"{s.day}–{fin.day} {MESES[s.month - 1]}"
    else:
        rango = f"{s.day} {MESES[s.month - 1]} – {fin.day} {MESES[fin.month - 1]}"
    return f"Semana {num}, {rango} {fin.year}"


def rango_dias(s: date, dias: int) -> str:
    fin = s + timedelta(days=dias - 1)
    nombres = {5: "lunes a viernes", 7: "lunes a domingo"}
    return f"{nombres.get(dias, '')}, {s.day} {MESES[s.month - 1]} – {fin.day} {MESES[fin.month - 1]}"


def etiqueta_corta(s: date) -> str:
    return f"{s.day} {MESES[s.month - 1]}"


def fecha_larga(dt: datetime) -> str:
    dt = timezone.localtime(dt)
    return f"{DIAS[dt.weekday()]} {dt.day} de {MESES[dt.month - 1]}, {dt:%H:%M}"
