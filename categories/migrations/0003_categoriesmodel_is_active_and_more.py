# Generated by Django 4.2.13 on 2024-05-10 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='categoriesmodel',
            name='is_active',
            field=models.BooleanField(blank=True, default=True, null=True),
        ),
        migrations.AddField(
            model_name='categoriesmodel',
            name='is_show_main',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
