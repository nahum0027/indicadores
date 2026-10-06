from django.db import migrations, models


class Migration(migrations.Migration):
    """Bajas por defunción; vacantes: operador -> ejecutivo de transporte, otras -> honorarios, sin mecánico."""

    dependencies = [
        ("core", "0008_quitar_queja_semaforo"),
    ]

    operations = [
        migrations.AddField(
            model_name="reporteadministracion",
            name="bajas_defuncion",
            field=models.PositiveIntegerField(default=0, help_text="", verbose_name="Bajas por defunción"),
        ),
        migrations.RenameField(model_name="reporteadministracion", old_name="vac_operador", new_name="vac_ejecutivo"),
        migrations.RenameField(model_name="reporteadministracion", old_name="vac_otro", new_name="vac_honorarios"),
        migrations.RemoveField(model_name="reporteadministracion", name="vac_mecanico"),
        migrations.AlterField(
            model_name="reporteadministracion",
            name="vac_ejecutivo",
            field=models.PositiveIntegerField(default=0, help_text="", verbose_name="Ejecutivo de transporte"),
        ),
        migrations.AlterField(
            model_name="reporteadministracion",
            name="vac_administrativo",
            field=models.PositiveIntegerField(default=0, help_text="", verbose_name="Administrativo"),
        ),
        migrations.AlterField(
            model_name="reporteadministracion",
            name="vac_honorarios",
            field=models.PositiveIntegerField(default=0, help_text="", verbose_name="Honorarios"),
        ),
    ]
