import os
import joblib

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.paginator import Paginator

from categories.models import CategoriesModel
from products.models import ProductModel

class Command(BaseCommand):
    # Aynı mağazada aynı isimdeki kategori özelliklerini tespit eder ve tekrarları siler

    def shop_category_match_fix(self, product, category):
        if category.name != product.category.name:
            from categories.models import CategoriesModel
            shop_category = CategoriesModel.objects.filter(is_deleted=False, match_id=product.category.id,
                                                           shop_id=product.shop.id).first()
            if shop_category is None:
                shop_category = CategoriesModel.objects.filter(is_deleted=False, id=product.category.id,
                                                               shop_id=product.shop.id).first()
            if shop_category is None:
                # product.category = category
                # product.save()
                pass
            print(f'{product.category.name}=={category.name}')
            # shop_category.match = category
            # shop_category.save()
        return category, product

    def predict_fix_unicode(self, predict):
        if predict == 'gıda & içecek':
            predict = 'gıda & İçecek'
        if predict == 'içecek hazırlama':
            predict = 'İçecek hazırlama'
        if predict == 'iç giyim':
            predict = 'İç giyim'
        if predict == 'araç içi aksesuarı':
            predict = 'araç İçi aksesuarı'
        if predict == 'araç içi telefon tutucu':
            predict = 'araç İçi telefon tutucu'
        if predict == 'dolap içi düzenleyici':
            predict = 'dolap İçi düzenleyici'
        if predict == 'sinek ilacı ve kovucu':
            predict = 'sinek İlacı ve kovucu'

        return predict

    def handle(self, *args, **options):
        if_not_check_categories = []
        if_not_check_products = []
        shop_categories = CategoriesModel.objects.filter(match__isnull=True, shop__isnull=False, is_deleted=False).exclude(
            shop=1).iterator()
        for category in shop_categories:
            print(category.id)
            is_match_category = CategoriesModel.objects.filter(shop__isnull=True, name__iexact=category.name, is_deleted=False).first()
            if is_match_category:
                print('eslesme var')
                print(category.name)
                category.match = is_match_category
                category.save()
            else:
                print('eslesme yok')
                print(category.name)

                query = ProductModel.objects.filter(category=category)
                model_path = os.path.join(settings.BASE_DIR, 'models_ai', 'main_category.pkl')
                main_model = joblib.load(model_path)

                paginator = Paginator(query, 100)

                print(f'{category.name} - {category.id} - {category.shop.id} - {query.count()}')
                if query.count() < 1:
                    category.is_deleted = True
                    category.save()

                predict_pool = {}
                for page_number in range(1, paginator.num_pages + 1):
                    print(f'page: {page_number} - {category.id}')
                    page_products = paginator.page(page_number)

                    for product in page_products:
                        category_name = product.category.name.replace('İ', 'i').lower()
                        if category_name in if_not_check_categories:
                            break
                        if product.id in if_not_check_products:
                            break
                        product_name = f'{product.category.name} {product.name}'
                        predict = main_model.predict([product_name])[0]
                        category1 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True, is_deleted=False).first()
                        model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category1.id}_category.pkl')
                        model = joblib.load(model_path)
                        predict = model.predict([product_name])[0]
                        predict = self.predict_fix_unicode(predict)
                        category2 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True, is_deleted=False).first()

                        # alt kategorisi yok ise
                        if category2 is not None:
                            is_exist = CategoriesModel.objects.filter(parent=category2.id, is_deleted=False).exists()
                            if not is_exist:
                                category_, product = self.shop_category_match_fix(product, category2)
                                try:
                                    predict_pool[category_.id].append(product.id)
                                except Exception as e:
                                    predict_pool[category_.id] = [product.id]

                            else:
                                model_path = os.path.join(settings.BASE_DIR, 'models_ai',
                                                          f'{category2.id}_category.pkl')
                                model = joblib.load(model_path)
                                predict = model.predict([product_name])[0]
                                predict = self.predict_fix_unicode(predict)
                                category3 = CategoriesModel.objects.filter(name__iexact=predict,
                                                                           shop__isnull=True, is_deleted=False).first()

                                # alt kategorisi yok ise
                                if category3 is not None:
                                    is_exist = CategoriesModel.objects.filter(parent=category3.id,
                                                                              is_deleted=False).exists()
                                    if not is_exist:
                                        category_, product = self.shop_category_match_fix(product, category3)
                                        try:
                                            predict_pool[category_.id].append(product.id)
                                        except Exception as e:
                                            predict_pool[category_.id] = [product.id]
                                    else:
                                        model_path = os.path.join(settings.BASE_DIR, 'models_ai',
                                                                  f'{category3.id}_category.pkl')
                                        model = joblib.load(model_path)
                                        predict = model.predict([product_name])[0]
                                        predict = self.predict_fix_unicode(predict)
                                        category4 = CategoriesModel.objects.filter(name__iexact=predict,
                                                                                   shop__isnull=True, is_deleted=False).first()
                                        if category4 is not None:
                                            # alt kategorisi yok ise
                                            is_exist = CategoriesModel.objects.filter(parent=category4.id,
                                                                                      is_deleted=False).exists()
                                            if not is_exist:
                                                category_, product = self.shop_category_match_fix(product, category4)
                                                try:
                                                    predict_pool[category_.id].append(product.id)
                                                except Exception as e:
                                                    predict_pool[category_.id] = [product.id]
                                            else:
                                                model_path = os.path.join(settings.BASE_DIR, 'models_ai',
                                                                          f'{category4.id}_category.pkl')
                                                model = joblib.load(model_path)
                                                predict = model.predict([product_name])[0]
                                                predict = self.predict_fix_unicode(predict)
                                                category5 = CategoriesModel.objects.filter(name__iexact=predict,
                                                                                           shop__isnull=True, is_deleted=False).first()
                                                # alt kategorisi yok ise
                                                if category5 is not None:
                                                    is_exist = CategoriesModel.objects.filter(parent=category5.id,
                                                                                              is_deleted=False).exists()
                                                    if not is_exist:
                                                        category_, product = self.shop_category_match_fix(product, category5)
                                                        try:
                                                            predict_pool[category_.id].append(product.id)
                                                        except Exception as e:
                                                            predict_pool[category_.id] = [product.id]
                                                    else:
                                                        try:
                                                            predict_pool[category5.id].append(product.id)
                                                        except Exception as e:
                                                            predict_pool[category5.id] = [product.id]
                print('*****tahmin****')
                print(predict_pool)
                if predict_pool:
                    max_key = max(predict_pool, key=lambda k: len(predict_pool[k]))
                    print(max_key)
                    cat = CategoriesModel.objects.filter(id=max_key).first()
                    print(f'{category.name}=={cat.name}')
                    category.match = cat
                    category.save()