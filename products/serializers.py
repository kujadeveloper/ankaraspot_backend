from rest_framework import serializers

from attachment.serializers import AttachmentSerializer, AttachmentComponentsSerializer
from brands.serializers import BrandElasticSerializer
from categories.serializers import CategoryElasticSerializer
from shops.serializers import ShopElasticSerializer, SubMerchantElasticSerializer,ShopDetailSerializer
from users.serializers import UserSerializer, UserViewSerializer
from .models import *


class ProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductModel
        fields = '__all__'


class ProductPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPriceModel
        fields = '__all__'


class ProductMatchSaltSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    shop = ShopElasticSerializer(read_only=True)
    sub_merchant_shop = SubMerchantElasticSerializer(read_only=True)

    class Meta:
        model = ProductModel
        fields = ['id',
                  'name',
                  'shop',
                  'link',
                  'image',
                  'sub_merchant_shop',
                  'price',
                  'is_deleted',
                  'cargo_price',
                  'updated_at']


class ProductMatchSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    shop = ShopElasticSerializer(read_only=True)
    sub_merchant_shop = SubMerchantElasticSerializer(read_only=True)
    price_history = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = ['id',
                  'name',
                  'shop',
                  'link',
                  'image',
                  'sub_merchant_shop',
                  'price',
                  'price_history',
                  'is_deleted',
                  'cargo_price',
                  'updated_at']

    def get_price_history(self, obj):
        if hasattr(obj, 'price_history') and obj.price_history is not None:  # Check for None
            try:
                if isinstance(obj.price_history, list):
                    if len(obj.price_history) > 0:
                        prices = obj.price_history[:5]
                        return ProductPriceSerializer(prices, many=True).data
                else:
                    prices = obj.price_history.all()[:5]
                    return ProductPriceSerializer(prices, many=True).data
            except AttributeError:
                return []
        return []
    

class ProductsMySerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    shop = ShopElasticSerializer(read_only=True)
    sub_merchant_shop = SubMerchantElasticSerializer(read_only=True)
    brand = BrandElasticSerializer(read_only=True)
    category = CategoryElasticSerializer(read_only=True)
    events = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = ['id',
                  'name',
                  'slug',
                  'barcode',
                  'model_code',
                  'link',
                  'image',
                  'shop',
                  'sub_merchant_shop',
                  'brand',
                  'price',
                  'stock',
                  'category',
                  'cargo_price',
                  'updated_at',
                  'match',
                  'events',
                  'is_deleted']

    def get_events(self, instance):
        response = instance.event_product.all()
        return ProductEventSerializer(response, many=True).data


class ProductsElasticSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    shop = ShopElasticSerializer(read_only=True)
    sub_merchant_shop = SubMerchantElasticSerializer(read_only=True)
    brand = BrandElasticSerializer(read_only=True)
    category = CategoryElasticSerializer(read_only=True)
    match = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = ['id',
                  'name',
                  'slug',
                  'barcode',
                  'model_code',
                  'link',
                  'image',
                  'shop',
                  'sub_merchant_shop',
                  'brand',
                  'price',
                  'category',
                  'cargo_price',
                  'is_deleted',
                  'updated_at',
                  'match']

    def get_match(self, obj):
        if obj.match is not None:
            matches = obj.match
            return ProductMatchSerializer(matches, many=True).data
        return []

class ProductFavoriteSerializer(serializers.ModelSerializer):
    product = ProductsElasticSerializer(read_only=True, many=False)

    class Meta:
        model = ProductFavoriteModel
        fields = ProductsElasticSerializer.Meta.fields

    def to_representation(self, instance):
        # Temel serileştirilmiş veriyi alın
        representation = instance
        # ProductModel serileştirilmiş verisini alın
        product_representation = ProductsElasticSerializer(instance.product).data if instance.product else {}
        data = {}
        for key in product_representation:
            data[key] = product_representation[key]
        return data


class ProductCommentSerializer(serializers.ModelSerializer):
    user = UserViewSerializer(read_only=True)
    user_rate = serializers.SerializerMethodField()

    class Meta:
        model = ProductCommentModel
        fields = ['id', 'product', 'user', 'comment', 'status', 'created_at', 'updated_at', 'user_rate']

    def get_user_rate(self, obj):
        # Yorumu yapan kullanıcının bu ürün için verdiği puanı bul
        if obj.product and obj.user:
            rate = ProductRateModel.objects.filter(
                id__in=obj.product.rate.filter(is_deleted=False).values_list('id', flat=True),
                user=obj.user,
                is_deleted=False
            ).first()
            return rate.rate if rate else obj.rating or None
        return obj.rating or None


class ProductsDetailSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    shop = ShopDetailSerializer(read_only=True)
    sub_merchant_shop = SubMerchantElasticSerializer(read_only=True)
    brand = BrandElasticSerializer(read_only=True)
    category = CategoryElasticSerializer(read_only=True)
    match = serializers.SerializerMethodField()
    spec_values = serializers.SerializerMethodField()
    price_history = serializers.SerializerMethodField()
    rate = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()

    class Meta:
        model = ProductModel
        fields = ['id',
                  'name',
                  'slug',
                  'description',
                  'barcode',
                  'command_count',
                  'model_code',
                  'link',
                  'image',
                  'shop',
                  'sub_merchant_shop',
                  'brand',
                  'price',
                  'spec_values',
                  'price_history',
                  'category',
                  'video_url',
                  'cargo_price',
                  'updated_at',
                  'match',
                  'rate',
                  'comment',
                  'is_deleted']

    def get_match(self, obj):
        if obj.match.exists():
            matches = obj.match.filter(is_deleted=False)
            return ProductMatchSerializer(matches, many=True).data
        return []

    def get_rate(self, obj):
        query = obj.rate.filter(is_deleted=False)
        point = query.aggregate(total_rate=models.Sum('rate'))['total_rate'] or 0
        total = query.count()
        possible_total_rate = total * 5
        percent = (point / possible_total_rate) * 100 if possible_total_rate else 0
        percent = (percent * 5) / 100
        return percent

    def get_spec_values(self, obj):
        specs_values = obj.spec_values.filter(is_deleted=False, is_active=True).select_related('specs')
        print("*********************SPEC VALUES:", specs_values)
        
        arr = []
        # Her bir value için spec bilgisini de ekle
        for val in specs_values:
            if val.specs:
                arr.append({
                    'spec': {
                        'id': val.specs.id,
                        'name': val.specs.name
                    },
                    'value': {
                        'id': val.id,
                        'value': val.value
                    }
                })
        return arr

    def get_price_history(self, obj):
        prices = obj.price_history.filter(is_deleted=False).order_by('id')[:5]
        return ProductPriceSerializer(prices, many=True).data

    def get_comment(self, obj):
        comments = obj.product_comments.filter(is_deleted=False).order_by('-created_at')
        return ProductCommentSerializer(comments, many=True).data


class ProductEventClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductUserClickModel
        fields = '__all__'


class ProductEventSerializer(serializers.ModelSerializer):
    click = ProductEventClickSerializer(read_only=True, many=True)
    product = ProductsElasticSerializer(read_only=True, many=False)

    class Meta:
        model = ProductEventModel
        fields = '__all__'


class ProductSaveEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductEventModel
        fields = '__all__'


class ProductDiscountSerializer(serializers.ModelSerializer):
    product = ProductsElasticSerializer(read_only=True)

    class Meta:
        model = ProductDiscountModel
        fields = ProductsElasticSerializer.Meta.fields

    def to_representation(self, instance):
        # Temel serileştirilmiş veriyi alın
        representation = instance
        # ProductModel serileştirilmiş verisini alın
        product_representation = ProductsElasticSerializer(instance.product).data if instance.product else {}
        data = {}
        for key in product_representation:
            data[key] = product_representation[key]
        return data


class ProductSearchHistorySerializer(serializers.ModelSerializer):
    user_username = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductSearchHistoryModel
        fields = ['id', 'user', 'user_username', 'search_term', 'search_type', 'created_at']
    
    def get_user_username(self, obj):
        if obj.user:
            return obj.user.username
        return None
