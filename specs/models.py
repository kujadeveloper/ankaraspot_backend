from django.db import models
from shops.models import ShopModel

class SpecsModel(models.Model):
    class Meta:
        ordering = ['-id']

    name = models.CharField(max_length=500, blank=True, null=True)
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='specs_shop', blank=True, null=True)
    value = models.ManyToManyField('SpecValueModel', blank=True, related_name='specs_value')

    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return self.name

class SpecValueModel(models.Model):
    class Meta:
        ordering = ['-id']

    value = models.CharField(max_length=200, blank=True, null=True)
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='spec_value_shop', blank=True, null=True)
    specs = models.ForeignKey(SpecsModel, on_delete=models.CASCADE, related_name='spec_values', blank=True, null=True)

    is_deleted = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_active = models.BooleanField(default=True, blank=True, null=True)

    def __str__(self):
        return self.value
