from rest_framework import serializers
from .models import ShopComparisonModel
from products.serializers import ProductsElasticSerializer

class ShopComparisonSerializer(serializers.ModelSerializer):
    product_details = ProductsElasticSerializer(source='product', read_only=True)
    competitor_product_details = ProductsElasticSerializer(source='competitor_product', read_only=True)
    competitor_shop_name = serializers.CharField(source='competitor_shop.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    competitor_product_slug = serializers.CharField(source='competitor_product.slug', read_only=True)
    
    class Meta:
        model = ShopComparisonModel
        fields = [
            'id',
            'product',
            'product_details',
            'product_slug',
            'competitor_product',
            'competitor_product_details',
            'competitor_product_slug',
            'competitor_shop',
            'competitor_shop_name',
            'price_difference',
            'price_difference_percentage',
            'is_cheaper',
            'last_updated'
        ]
        read_only_fields = ['price_difference', 'price_difference_percentage', 'is_cheaper', 'last_updated'] 