from django.core.management.base import BaseCommand

from categories.models import CategoriesModel
from products.models import ProductModel

class Command(BaseCommand):
    help = 'Ürünleri matchleşen kategorilere taşır.'

    def handle(self, *args, **options):
        categories = CategoriesModel.objects.values('name', 'id', 'match').filter(is_deleted=False, shop__isnull=False,
                                                                                  match__isnull=False)
        categories_count = categories.count()
        categories_all = categories.iterator()
        for category in categories_all:
            categories_count = categories_count - 1
            print(f"{category['name']} : {category['id']} : {categories_count}")
            products = ProductModel.objects.filter(category=category['id'], is_deleted=False)
            page_size = 10
            total_count = products.count()
            print(f' Güncellenecek products sayısı: {products.count()}')
            all_products = products.iterator()

            if total_count > 0:
                match = CategoriesModel.objects.filter(id=category['match']).first()

            for product in all_products:
                product.category = match
                product.save()
            print(f' Tamamlandı: {str(total_count)}')