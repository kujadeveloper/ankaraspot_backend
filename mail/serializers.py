from rest_framework import serializers

from utils.utils import generate_custom_random_key, custom_hash

from users.models import User

from .models import MailModel


class MailSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = MailModel
        fields = '__all__'

    def create_token(self, user, mail_type):
        if mail_type == 0:
            custom_key = generate_custom_random_key(20, use_punctuation=True)
            user = User.objects.filter(email=user).first()
            user.mail_confirm_key = custom_hash(custom_key)
            user.save()
            return True
        return False

    def create(self, validated_data):
        mail_type = validated_data.pop('mail_type', None)
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
