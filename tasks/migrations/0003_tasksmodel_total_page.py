# Generated by Django 5.1.2 on 2024-12-26 10:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_alter_tasksmodel_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='tasksmodel',
            name='total_page',
            field=models.IntegerField(default=0),
        ),
    ]
