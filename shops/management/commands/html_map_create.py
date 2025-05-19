from django.core.management.base import BaseCommand

from shops.models import ShopModel, HtmlFieldModel


class Command(BaseCommand):
    help = 'Html map create..'

    def handle(self, *args, **kwargs):
        shops = ShopModel.objects.filter(is_deleted=False, sync_service=7)
        for shop in shops:
            print(shop.id)
            print(shop.html_map.exists())
            field = HtmlFieldModel.objects.filter(id=4172).first()
            if not shop.html_map.exists():
                shop.html_map.add(field)
