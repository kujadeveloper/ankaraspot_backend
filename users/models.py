from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    class Meta:
        verbose_name_plural = "Kullanıcılar"  # Plural name
        ordering = ['id']
        db_table = 'users'


    user = models.ForeignKey('user', on_delete=models.CASCADE, blank=True, null=True, related_name='user_user')
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    confirm_code = models.CharField(max_length=6, blank=True, null=True)
    last_name = models.CharField(max_length=30)
    birtday = models.DateTimeField(blank=True, null=True)
    company = models.CharField(max_length=250, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True, null=True)
    district = models.CharField(max_length=250, blank=True, null=True)
    gender = models.IntegerField(default=0, blank=True, null=True)
    phone = models.CharField(max_length=15)
    anonym = models.UUIDField(default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=255, blank=True, null=True)
    confirm_token = models.CharField(max_length=500, blank=True, null=True)
    tax_number = models.CharField(max_length=30, blank=True, null=True)
    shop = models.ForeignKey('shops.ShopModel', on_delete=models.CASCADE, blank=True,
                             null=True, related_name='user_shop')

    is_active = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        self.is_deleted = False
        self.save()


class SshKeyModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'ssh_keys'

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='user_ssh_key')
    name = models.CharField(max_length=200)
    ssh_key = models.CharField(max_length=1000)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        self.is_deleted = False
        self.save()


class SubScribeModel(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='user_subscribe')
    email = models.CharField(max_length=200)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        self.is_deleted = False
        self.save()

class NotificationModel(models.Model):
    class Meta:
        ordering = ['-created_at']
        db_table = 'notifications'

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='user_notifications')
    subject = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)