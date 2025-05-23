# Generated by Django 4.2.13 on 2024-05-11 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('shops', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SynchronizeModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('error', models.TextField(blank=True, null=True)),
                ('data', models.JSONField(blank=True, null=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('shop', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='synchronize_shop', to='shops.shopmodel')),
            ],
            options={
                'db_table': 'synchronize_error',
                'ordering': ['id'],
            },
        ),
    ]
