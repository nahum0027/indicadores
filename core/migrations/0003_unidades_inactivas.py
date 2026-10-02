from django.db import migrations, models


def sumar_motivos(apps, schema_editor):
    """Pasa los inactivos que ya estaban capturados por motivo al nuevo campo único."""
    Reporte = apps.get_model("core", "ReporteOperaciones")
    for r in Reporte.objects.all():
        r.unidades_inactivas = r.inhab_taller + r.inhab_siniestro + r.inhab_documentacion + r.inhab_otro
        r.save(update_fields=["unidades_inactivas"])


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_perfil"),
    ]

    operations = [
        migrations.AddField(
            model_name="reporteoperaciones",
            name="unidades_inactivas",
            field=models.PositiveIntegerField(
                default=0, help_text="Unidades que no operaron (taller, siniestro, documentación, etc.)",
                verbose_name="Unidades inactivas"),
        ),
        migrations.RunPython(sumar_motivos, migrations.RunPython.noop),
        migrations.RemoveField(model_name="reporteoperaciones", name="inhab_documentacion"),
        migrations.RemoveField(model_name="reporteoperaciones", name="inhab_otro"),
        migrations.RemoveField(model_name="reporteoperaciones", name="inhab_siniestro"),
        migrations.RemoveField(model_name="reporteoperaciones", name="inhab_taller"),
    ]
