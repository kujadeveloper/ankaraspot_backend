import time

from django.core.management.base import BaseCommand

from products.models import ProductModel
from products.tasks import upload_images
from synchronize_error.models import SynchronizeModel
from django.db.models import Q
from utils.utils import parent_match
from django.core.paginator import Paginator


class Command(BaseCommand):
    help = 'Product barcode matching..'

    def handle(self, *args, **options):
        while True:
            query = ProductModel.objects.filter(barcode__isnull=False, is_deleted=False).filter(Q(is_match=False),
                                                                                                Q(match__isnull=True))
            paginator = Paginator(query, 100)
            total_pages = paginator.num_pages
            print(f"Toplam sayfa sayısı: {total_pages}")

            for i in range(0, total_pages + 1):
                print(f'page: {str(i)}')
                products = paginator.get_page(i)
                for product in products:
                    # TODO eşleşmiş olanı varmı
                    is_match = ProductModel.objects.filter(barcode=product.barcode, match__isnull=False).exclude(
                        id=product.id).first()
                    if is_match:
                        product = ProductModel.objects.filter(id=product.id).first()
                        product.is_match = True
                        product.save()
                        is_match.match.add(product)
                    else:
                        # TODO is match olanı varmı
                        is_match = ProductModel.objects.filter(barcode=product.barcode, is_match=True).exclude(
                            id=product.id).first()
                        if is_match:
                            parent_id = parent_match(is_match.id)
                            is_match = ProductModel.objects.filter(id=parent_id).exclude(id=product.id).first()
                            if is_match is not None:
                                product.is_match = True
                                product.save()
                                is_match.match.add(product)
                        else:
                            # TODO aynı barcode olanı varmı aktif urunlerden
                            is_match = ProductModel.objects.filter(barcode=product.barcode, is_deleted=False).exclude(
                                id=product.id).first()
                            if is_match:
                                product = ProductModel.objects.filter(id=product.id).first()
                                product.is_match = True
                                product.save()
                                is_match.match.add(product)
                            else:
                                # TODO aynı barcode olanı varmı silinmişlerden
                                is_match = ProductModel.objects.filter(barcode=product.barcode,
                                                                       is_deleted=True).exclude(id=product.id).first()
                                if is_match:
                                    product = ProductModel.objects.filter(id=product.id).first()
                                    is_match.is_match = True
                                    is_match.save()
                                    product.match.add(is_match)

                    print(product)
            time.sleep(3600)