from django.core.management.base import BaseCommand
from products.models import ProductModel

from utils.youtube_api import Youtube


class Command(BaseCommand):
    help = 'Youtube videoları cek'
    def handle(self, *args, **options):
        youtube = Youtube()
        products = ProductModel.objects.filter(is_deleted=False, video_url__isnull=True).iterator()
        for product in products:
            for product in products:
                try:
                    video = youtube.search(product.name)
                    if video:
                        product.video_url = video
                        product.save()
                except Exception as e:
                    print(f"Error processing product {product.id}: {str(e)}")
                    continue
