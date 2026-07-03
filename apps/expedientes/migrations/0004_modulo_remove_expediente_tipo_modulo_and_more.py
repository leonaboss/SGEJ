from django.db import migrations, models
import django.db.models.deletion


def insert_modulos(apps, schema_editor):
    Modulo = apps.get_model('expedientes', 'Modulo')
    if Modulo.objects.count() == 0:
        modulos_data = [
            ('DESP', 'Calificación de Despido / Recientes'),
            ('INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'),
            ('OFIC', 'Expedientes en Oficina Consultoría Jurídica'),
            ('CONT', 'Contrataciones y Convenios de la Universidad'),
            ('LITI', 'Litigios Judiciales y Administrativos'),
            ('SUST', 'Sustanciación de Procedimientos Disciplinarios'),
            ('IND', 'Índices de Inspectoría del Trabajo'),
        ]
        for nombre, descripcion in modulos_data:
            Modulo.objects.create(nombre=nombre, descripcion=descripcion)


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0003_alter_cargo_options_alter_motivo_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Modulo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(choices=[('DESP', 'Calificación de Despido / Recientes'), ('INSP', 'Casos de Inspectoría / Horas Extra / Reclamos'), ('OFIC', 'Expedientes en Oficina Consultoría Jurídica'), ('CONT', 'Contrataciones y Convenios de la Universidad'), ('LITI', 'Litigios Judiciales y Administrativos'), ('SUST', 'Sustanciación de Procedimientos Disciplinarios'), ('IND', 'Índices de Inspectoría del Trabajo')], max_length=4, unique=True)),
                ('descripcion', models.TextField(blank=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Módulos',
                'db_table': 'modulos',
                'ordering': ['-created_at'],
            },
        ),
        migrations.RunPython(insert_modulos, reverse_code=migrations.RunPython.noop),
        migrations.AddField(
            model_name='expediente',
            name='modulo',
            field=models.ForeignKey(blank=True, db_column='modulo_id', null=True, on_delete=django.db.models.deletion.PROTECT, to='expedientes.modulo'),
        ),
        migrations.RemoveField(
            model_name='expediente',
            name='tipo_modulo',
        ),
        migrations.AlterField(
            model_name='expediente',
            name='tipo_demanda',
            field=models.TextField(blank=True, null=True),
        ),
    ]
