# Generated by Django 4.2.13 on 2024-05-11 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_remove_productmodel_stock_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productmodel',
            name='slug',
            field=models.SlugField(max_length=255, unique=True),
        ),
    ]
