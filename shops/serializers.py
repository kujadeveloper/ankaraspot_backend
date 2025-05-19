from rest_framework import serializers

from attachment.serializers import AttachmentComponentsSerializer
from brands.serializers import BrandSerializer
from products.models import ProductModel
from .models import ShopModel, SubMerchantModel, ShopCommentModel, HtmlFieldModel


class ShopSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(many=False, read_only=True)

    class Meta:
        model = ShopModel
        fields = '__all__'

class ShopHtmlSerializer(serializers.ModelSerializer):
    class Meta:
        model = HtmlFieldModel
        fields = '__all__'

class ShopPublicSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(many=False, read_only=True)
    html_map = ShopHtmlSerializer(many=True, read_only=True)
    product_count = serializers.SerializerMethodField()
    class Meta:
        model = ShopModel
        fields = ('id', 'name', 'shop_title', 'web_url', 'images', 'url', 'cargo_barem', 'is_deleted', 'sync_service', 'is_active_sync', 'is_active', 'html_map', 'product_count')

    def get_product_count(self, obj):
        active = ProductModel.objects.filter(shop=obj, is_deleted=False, image__isnull=False).count()
        pasive = ProductModel.objects.filter(shop=obj, is_deleted=True).count()
        pasive_ = ProductModel.objects.filter(shop=obj, is_deleted=False, image__isnull=True).count()
        return {'active':active, 'pasive': pasive+pasive_}

class ShopMeSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(many=False, read_only=True)
    tax_document = AttachmentComponentsSerializer(many=False, read_only=True)

    class Meta:
        model = ShopModel
        fields = '__all__'


class ShopCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopCommentModel
        fields = '__all__'


class ShopElasticSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(many=False)

    class Meta:
        model = ShopModel
        fields = ['id', 'name', 'shop_title', 'images']

class ShopDetailSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(many=False)
    brands = BrandSerializer(many=True, read_only=True)
    class Meta:
        model = ShopModel
        fields = ['id', 'name', 'shop_title', 'images', 'shop_description', 'brands', 'cargo_barem']

class SubMerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubMerchantModel
        fields = '__all__'


class SubMerchantElasticSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubMerchantModel
        fields = ['id', 'name']