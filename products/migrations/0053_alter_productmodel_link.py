# Generated by Django 5.1.2 on 2025-04-13 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0052_productsearchhistorymodel'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productmodel',
            name='link',
            field=models.URLField(max_length=2000),
        ),
    ]
