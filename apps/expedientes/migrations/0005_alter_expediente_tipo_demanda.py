from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0004_modulo_remove_expediente_tipo_modulo_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expediente',
            name='tipo_demanda',
            field=models.TextField(blank=True, null=True),
        ),
    ]
