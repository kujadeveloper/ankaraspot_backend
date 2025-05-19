from django.db import models
from products.models import ProductModel
from shops.models import ShopModel

class ShopComparisonModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'shop_comparisons'
        verbose_name_plural = "Mağaza Karşılaştırmaları"

    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='comparison_product')
    competitor_product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='comparison_competitor_product')
    competitor_shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, related_name='comparison_competitor_shop')
    
    price_difference = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    price_difference_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    is_cheaper = models.BooleanField(default=False)
    
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
