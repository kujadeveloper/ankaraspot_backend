from rest_framework import serializers

from attachment.serializers import AttachmentComponentsSerializer
from shops.serializers import ShopElasticSerializer
from .models import CategoriesModel

class CategoriesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriesModel
        fields = ['id', 'name', 'bread_crumb']

class CategoriesSerializer(serializers.ModelSerializer):
    shop = ShopElasticSerializer(read_only=True)
    match = serializers.SerializerMethodField()
    images = AttachmentComponentsSerializer(read_only=True)
    specs = serializers.SerializerMethodField()

    class Meta:
        model = CategoriesModel
        fields = '__all__'

    def get_match(self, obj):
        if obj.match:
            # Recursively call the serializer but manage depth as needed
            return CategoryElasticSerializer(obj.match).data
        return None

    def get_specs(self, obj):
        return obj.specs.filter(is_active=True).values()

class CategoriesMenuSerializer(serializers.ModelSerializer):
    images = AttachmentComponentsSerializer(read_only=True)
    class Meta:
        model = CategoriesModel
        fields = ['id', 'name', 'parent', 'slug', 'images']

class CategoriesBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriesModel
        fields = ('id', 'name', 'slug')

class CategoriesChildSerializer(serializers.ModelSerializer):
    shop = ShopElasticSerializer(read_only=True)
    children = CategoriesSerializer(many=True, read_only=True)
    class Meta:
        model = CategoriesModel
        fields = '__all__'


class CategoryElasticSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriesModel
        fields = ['id', 'name', 'bread_crumb', 'slug', 'is_adult']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['bread_crumb'] = list(representation['bread_crumb'])

        return representation