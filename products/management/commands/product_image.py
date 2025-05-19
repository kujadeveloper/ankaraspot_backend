import time

from django.core.management.base import BaseCommand

from products.tasks import upload_images
from synchronize_error.models import SynchronizeModel
from django.db.models import Q


class Command(BaseCommand):
    help = 'Resmi yüklenmemiş ürünlerin resmini yükler..'

    def handle(self, *args, **options):
        while True:
            print('start')
            all_datas = SynchronizeModel.objects.filter(
                Q(error='Ürün bulunamadı') &
                (Q(try_count__isnull=True) | Q(try_count__lt=10))
            )[:100]
            print('count:',all_datas.count())
            for data in all_datas:
                print(data.id)
                try:
                    upload_images(data.data, product_id=data.product)
                    data.delete()
                    print('ok')
                except Exception as e:
                    print(e)
                    if data.try_count is None:
                        data.try_count = 1
                    else:
                        data.try_count = data.try_count + 1
                    data.save()
            print('end wait 60 sec.')
            time.sleep(5)