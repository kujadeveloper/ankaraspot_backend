from rest_framework import serializers
from .models import BrandModel
from attachment.serializers import AttachmentComponentsSerializer

class BrandSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(many=False)
    class Meta:
        model = BrandModel
        fields = '__all__'


class BrandElasticSerializer(serializers.ModelSerializer):
    class Meta:
        model = BrandModel
        fields = ['id', 'name']