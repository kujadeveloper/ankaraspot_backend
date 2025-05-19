from django.contrib import admin
from .models import ShopComparisonModel

@admin.register(ShopComparisonModel)
class ShopComparisonAdmin(admin.ModelAdmin):
    list_display = ('product', 'competitor_product', 'competitor_shop', 'price_difference', 'is_cheaper', 'last_updated')
    list_filter = ('is_cheaper', 'competitor_shop', 'is_deleted')
    search_fields = ('product__name', 'competitor_product__name', 'competitor_shop__name')
    date_hierarchy = 'created_at'
