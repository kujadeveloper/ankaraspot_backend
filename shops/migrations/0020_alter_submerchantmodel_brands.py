# Generated by Django 5.1.2 on 2024-11-09 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('brands', '0004_alter_brandmodel_options'),
        ('shops', '0019_alter_shopmodel_brands_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submerchantmodel',
            name='brands',
            field=models.ManyToManyField(blank=True, to='brands.brandmodel'),
        ),
    ]
