from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("config", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="salachat",
            name="descripcion",
        ),
        migrations.RemoveField(
            model_name="incidencia",
            name="nota_admin",
        ),
    ]
