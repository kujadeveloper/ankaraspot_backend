from django.db.models.signals import post_save, pre_save, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from .models import ProductModel


@receiver(post_save, sender=ProductModel)
def send_product_match(sender, instance, created, **kwargs):
    """Ürün silindiğinde match'leri temizle"""
    if not created and instance.is_deleted and instance.is_match:
        with transaction.atomic():
            instance.match.clear()
            ProductModel.objects.filter(id=instance.id).update(is_match=False)


