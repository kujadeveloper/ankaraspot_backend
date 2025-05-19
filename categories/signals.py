from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import CategoriesModel


#category değiştiğinde cache sil
@receiver(post_save, sender=CategoriesModel)
def delete_cache(sender, instance, created, **kwargs):
    cache.delete('all_categories')


