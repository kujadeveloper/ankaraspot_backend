from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group

from rest_framework import serializers

from shops.serializers import ShopSerializer, ShopMeSerializer
from users.models import User, SshKeyModel, SubScribeModel, NotificationModel
from datetime import datetime


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationModel
        fields = ['id', 'subject', 'title', 'content', 'status', 'created_at']


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name']


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'email', 'last_name']


class UserMeSerializer(serializers.ModelSerializer):
    groups = GroupSerializer(many=True, read_only=True)
    shop = ShopMeSerializer(many=False, read_only=True)
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'groups', 'shop', 'phone', 'tax_number', 'birtday', 'city', 'district', 'gender')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            try:
                validate_password(password)
            except ValidationError as e:
                print(e)  # Handle the error by informing the user of password requirements
                raise serializers.ValidationError(e)
            instance.set_password(password)

        instance.save()
        return instance

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password is not None:
            try:
                validate_password(password)
            except ValidationError as e:
                print(e)  # Handle the error by informing the user of password requirements
                raise serializers.ValidationError(e)

            instance.set_password(password)

        instance.save()
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Yeni şifre en az 8 karakter olmalıdır.")
        return value
    
class SshKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = SshKeyModel
        fields = '__all__'


class SubScribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubScribeModel
        fields = '__all__'
