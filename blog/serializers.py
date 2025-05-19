from rest_framework import serializers
from .models import BlogModel
from attachment.serializers import AttachmentComponentsSerializer

class BlogSerializer(serializers.ModelSerializer):
    image = AttachmentComponentsSerializer(read_only=True)
    
    class Meta:
        model = BlogModel
        fields = ('id', 'title', 'content', 'slug', 'created_at', 'updated_at', 'status', 'image')