# Generated by Django 5.1.2 on 2024-11-12 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shops', '0021_htmlfieldmodel_shopmodel_html_map'),
    ]

    operations = [
        migrations.AddField(
            model_name='htmlfieldmodel',
            name='priority',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
