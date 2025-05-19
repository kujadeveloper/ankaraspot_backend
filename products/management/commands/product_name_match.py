import time
from django.core.management.base import BaseCommand
from utils.utils import parent_match
from products.models import ProductModel
from tasks.models import TasksModel
from products.documents import ProductDocument
class Command(BaseCommand):
    help = 'Product name matching..'

    def handle(self, *args, **options):
        while True:
            products = (ProductModel.objects.filter(is_match=False, match__isnull=True, is_deleted=False)
                        .only('id', 'is_match', 'match').iterator())
            for product in products:
                if product.is_match:
                    break
                if product.match.exists():
                    break
                start_time = time.time()
                # TODO bir ürünün ismini al ve elasticsearch üzerinde benzerlerini getir.
                if product.name is not None:
                    search = ProductDocument.search().query("multi_match", query=product.name, fields=['name^5'])
                    response = search.execute()
                    matches_to_create = []
                    #isim uzunluguna göre score ver
                    print(len(product.name))
                    name_len = len(product.name)

                    score = 210
                    if 0 < name_len < 35:
                        score = 150
                    elif 35 <= name_len < 50:
                        score = 180
                    elif 50 <= name_len < 70:
                        score = 200



                    for hit in response:
                        item = hit.to_dict()
                        item['score'] = hit.meta.score
                        print(item['id'], product.id, item['score'], score)
                        if hit.meta.score > score:
                            # print(hit.meta.score)
                            # TODO buldugu ürün kendisi değilse.
                            if item['id'] != product.id:
                                # TODO buldugu ürün ile aradığım ürünün marka ismi aynımı
                                # if item['brand']['name'].lower() == product.brand.name.lower():
                                # if item['price'] == product.price:
                                # print(item['name'] + '==' + product.name)
                                # print(str(item['id']) + '==' + str(product.id))
                                prd = ProductModel.objects.filter(id=item['id']).first()
                                # TODO buldugumuz ürün herhangi bir seyin altında matchleşmişmi
                                if prd is not None:
                                    if prd.is_match:
                                        parent_id = parent_match(prd.id)
                                        is_match = ProductModel.objects.filter(id=parent_id).exclude(
                                            id=prd.id).first()
                                        product.is_match = True
                                        product.save()
                                        if is_match is not None:
                                            is_match.match.add(product)
                                    else:
                                        # TODO buldugumuz ürünün altında matchleşmiş ürün varmı
                                        if prd.match.exists():
                                            product.is_match = True
                                            product.save()
                                            prd.match.add(product)
                                        else:
                                            # TODO ikli üründe eşleşmemişse bulunan ürünü altına at.
                                            prd.is_match = True
                                            prd.save()
                                            product.match.add(prd)
                    end_time = time.time()
                    print(f"{product.id} Fonksiyonun çalışma süresi: {end_time - start_time:.6f} saniye")

            time.sleep(60)