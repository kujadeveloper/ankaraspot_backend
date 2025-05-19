from django.db import models

from products.models import ProductModel
from shops.models import ShopModel


# Create your models here.
class SynchronizeModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'synchronize_error'

    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, blank=True, null=True, related_name='synchronize_shop')
    error = models.TextField(blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    script_file = models.TextField(blank=True, null=True)
    product = models.TextField(blank=True, null=True)
    try_count = models.IntegerField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SynchronizeUrlsModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'synchronize_url'

    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, blank=True, null=True, related_name='synchronize_url_shop')
    url = models.TextField(blank=True, null=True, db_index=True, unique=True)
    error = models.TextField(blank=True, null=True)
    html = models.TextField(blank=True, null=True)
    parent = models.ForeignKey("SynchronizeUrlsModel", blank=True, null=True, on_delete=models.SET_NULL,
                               related_name='children_urls')

    status = models.IntegerField(blank=True, null=True, default=0)
    host_name = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)