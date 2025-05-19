from rest_framework import serializers

from specs.models import SpecsModel, SpecValueModel


class SpecValueSerialziers(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = SpecValueModel
        fields = ['id', 'label']

    def get_label(self, obj):
        return obj.value

class SpecSerialziers(serializers.ModelSerializer):
    #value = SpecValueSerialziers(read_only=True, many=True)
    class Meta:
        model = SpecsModel
        fields = ['id','name']

class SpecCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    shop = serializers.IntegerField()
    value = serializers.ListField(
        child=serializers.CharField(max_length=255)
    )
    product_id = serializers.IntegerField(required=False, allow_null=True)
