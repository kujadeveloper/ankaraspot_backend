# Generated by Django 4.2.13 on 2024-07-02 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0027_productmodel_is_variant'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productmodel',
            name='is_variant',
        ),
    ]
