from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('brands', '0004_alter_brandmodel_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandmodel',
            name='is_popular',
            field=models.BooleanField(default=False),
        ),
    ]