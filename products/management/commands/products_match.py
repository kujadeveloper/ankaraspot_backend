from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from utils.utils import parent_match
from products.models import ProductModel
from products.documents import ProductDocument

class Command(BaseCommand):
    help = 'Product matching..'

    def search_similar_products(
            self,
            product: ProductModel,
            fields: list = ["name"],
            min_term_freq: int = 1,
            max_query_terms: int = 5,
            size: int = 10,
            similarity_threshold: float = 0.9  # %90 benzerlik eşiği
    ) -> dict:
        """
        %90'dan düşük benzerlikteki ürünleri filtreler.
        """
        try:
            # Sorguyu çalıştır
            more_like_this_query = {
                "more_like_this": {
                    "fields": fields,
                    "like": [{"_id": str(product.id)}],  # Ürün ID'si string'e çevriliyor
                    "min_term_freq": min_term_freq,  # Minimum terim frekansı
                    "max_query_terms": max_query_terms  # Maksimum sorgu terimi sayısı
                }
            }

            filters = [
                {'term': {'brand.id': product.brand.id}},
                {'term': {'category.id': product.category.id}}
            ]
            search = ProductDocument.search().query(
                'bool',
                must=[more_like_this_query],
                filter=filters
            )
            search = search[0:size]
            response = search.execute()

            # Eğer sonuç yoksa boş dön
            if not response.hits:
                return {"hits": [], "total": 0}

            # En yüksek skoru bul (referans)
            max_score = max(hit.meta.score for hit in response.hits)

            # Minimum kabul edilebilir skoru hesapla (%90 eşik)
            min_acceptable_score = max_score * similarity_threshold
            print(min_acceptable_score)
            filtered_hits = []
            for hit in response.hits:
                print(hit.meta.score)
                if hit.meta.score >= min_acceptable_score:
                    print(hit.id)
                    print(f'{hit.name} == {product.name} : {hit.meta.score}')
                    print('****')
                    if hit.meta.score > 45:
                        filtered_hits.append(hit)

            return {
                "hits": filtered_hits,
                "total": len(filtered_hits),
                "max_score": max_score,
                "min_acceptable_score": min_acceptable_score
            }

        except Exception as e:
            return {"error": str(e), "hits": [], "total": 0}


    def handle(self, *args, **options):

        products = ProductModel.objects.filter(is_deleted=False, is_match=False, match__isnull=True).order_by('-id')
        paginator = Paginator(products, 1)
        page = 0
        while True:
            print(f'page: {page}')
            products = paginator.get_page(page)
            page = page + 1
            for product in products:
                print(product.id)
                result = self.search_similar_products(
                    product=product,
                    fields=["name", "category.name", "brand.name"],
                    min_term_freq=1,
                    max_query_terms=5,
                    size=100,
                    similarity_threshold = 0.9
                )
                # Process the results
                if not result.get("error"):
                    print(f"Found {result['total']} similar products")
                    # hepsine bir bak eşleşmiş bir ürün varmı ?
                    is_match_found = False
                    is_prd = None
                    for hit in result["hits"]:
                        prd = ProductModel.objects.filter(id=hit['id']).first()
                        if prd is not None:
                            if prd.is_match:
                                parent_id = parent_match(prd.id)
                                if parent_id is not None:
                                    is_prd = ProductModel.objects.get(id=parent_id)
                                    break
                        if prd.match.exists():
                            is_match_found = True
                            is_prd = prd

                    #buldugu urunler içinde eşleşmiş olan var.
                    if is_match_found:
                        print('eşleşiş ürün var.')
                        print(product.id)
                        if is_prd is not None:
                            is_prd.match.add(product)
                            is_prd.is_deleted = False
                            is_prd.save()
                            product.is_match=True
                            product.save()
                    else:
                        print('eşleşiş ürün yok.')
                        for hit in result["hits"]:
                            print(hit['id'])
                            ProductModel.objects.filter(id=hit['id']).update(is_match=True)
                            product.match.add(hit['id'])
                            product.is_deleted = False
                            product.save()
                else:
                    print(f"Error: {result['error']}")
