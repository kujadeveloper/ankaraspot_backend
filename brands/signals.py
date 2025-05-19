from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import BrandModel


#brand değiştiğinde cache sil
@receiver(post_save, sender=BrandModel)
def delete_cache(sender, instance, created, **kwargs):
    cache.delete('all_brands')


