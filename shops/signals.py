from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Q

from mail.models import MailModel
from users.models import User
from .models import ShopModel, SubMerchantModel
from products.models import ProductModel
from products.tasks import update_shop_elasticsearch_index

import json
import os

#update işleminde eğer product silinmiş ise match durumundanda cıkar
@receiver(post_save, sender=ShopModel)
def update_shop(sender, instance, created, **kwargs):
    if not created:
        # Mağaza aktiflik durumu takibi
        if hasattr(instance, '_original_is_active') and instance._original_is_active != instance.is_active:
            # Elasticsearch güncellemesini Celery task olarak asenkron işle
            # Mağaza aktif/pasif değişiminde ürünlerin görünürlüğünü güncelle (silme işlemi yapılmayacak)
            transaction.on_commit(lambda: update_shop_elasticsearch_index.delay(instance.id))
            
        if instance.is_active_sync:
            user = User.objects.filter(shop=instance.id, is_deleted=False).first()
            if user is not None:
                is_mail = MailModel.objects.filter(is_deleted=False, to=user.email, mail_type=2).exists()

                if not is_mail:
                    content = json.dumps({'shop_id': instance.id,
                                          'name': f'{user.first_name} {user.last_name}'})
                    MailModel.objects.create(user=user, mail_type=2, to=user.email,
                                             subject='FİYATOR ÜRÜNLERİNİZ YAYINA ALINDI', content=content)

