# Generated by Django 5.1.2 on 2025-02-04 07:04

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_alter_blogmodel_content'),
        ('categories', '0016_categoriesmodel_is_adult'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogmodel',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='categories.categoriesmodel', verbose_name='Kategori'),
        ),
        migrations.AlterField(
            model_name='blogmodel',
            name='content',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='blogmodel',
            name='status',
            field=models.BooleanField(default=True, verbose_name='Aktif/Pasif'),
        ),
        migrations.AlterField(
            model_name='blogmodel',
            name='title',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True),
        ),
    ]
