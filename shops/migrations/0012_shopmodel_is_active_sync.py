# Generated by Django 4.2.13 on 2024-08-15 07:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0011_shopmodel_trendyol_api_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopmodel',
            name='is_active_sync',
            field=models.BooleanField(default=False),
        ),
    ]
