# Generated by Django 5.1.2 on 2025-01-31 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0047_productcommentmodel_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='productmodel',
            name='final_score',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
        migrations.AddField(
            model_name='productmodel',
            name='match_score',
            field=models.IntegerField(blank=True, default=1, null=True),
        ),
        migrations.AddField(
            model_name='productmodel',
            name='shop_score',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='productmodel',
            name='total_match_count',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AddField(
            model_name='productmodel',
            name='total_shop_count',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
