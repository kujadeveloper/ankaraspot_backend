# Generated by Django 4.2.13 on 2024-08-23 12:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail', '0002_rename_mailtype_mailmodel_mail_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mailmodel',
            options={'ordering': ['id'], 'verbose_name_plural': 'Mail Listesi'},
        ),
    ]
