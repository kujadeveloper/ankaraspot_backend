from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Balance

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_balance(sender, instance, created, **kwargs):
    """Yeni kullanıcı oluşturulduğunda otomatik olarak bakiye oluştur"""
    if created:
        Balance.objects.create(user=instance, amount=0)
