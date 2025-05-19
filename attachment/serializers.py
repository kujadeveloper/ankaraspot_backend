from rest_framework import serializers
from .models import AttachmentModel


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttachmentModel
        fields = '__all__'

class AttachmentComponentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttachmentModel
        fields = ['id', 'thumb_file_url']


class AttachmentJustImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = AttachmentModel
        fields = ['image']

    def get_image(self, instance):
        return instance.thumb_file_url
