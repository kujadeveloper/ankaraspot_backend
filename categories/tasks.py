from celery import shared_task

def get_all_children(category):
    if category is not None:
        children = category.get_children()
        all_children = list(children)  # Start with the immediate children
    else:
        all_children = []

    # Recursively fetch children of each child category
    for child in children:
        all_children.extend(get_all_children(child))
    return all_children


@shared_task
def category_count():
    from products.models import ProductModel
    from categories.models import CategoriesModel
    categories = CategoriesModel.objects.filter(is_deleted=False, shop__isnull=True).all()
    for category in categories:
        children = get_all_children(category)
        ids = [child.id for child in children]
        ids.append(category.id)
        query = ProductModel.objects.filter(is_deleted=False, category__in=ids)
        count = query.count()
        product = query.first()
        category.product_count = count
        if product is not None:
            category.images = product.image
        category.save()


def recursive(item):
    from categories.models import CategoriesModel
    query = CategoriesModel.objects.filter(is_deleted=False, shop=None, parent=item).order_by('name')
    data_sub = query.all()
    arr = []
    for item in data_sub:
        print(item.name)
        arr.append({'id': item.id, 'name':item.name, 'child': recursive(item)})

    return arr

@shared_task
def category_cache():
    from django.core.cache import cache
    data = recursive(None)
    cache.delete('main_all_categories')
    cache.set('main_all_categories', data)
    return 'OK'

@shared_task
def category_match():
    from products.models import ProductModel
    from categories.models import CategoriesModel
    import joblib
    import os
    from django.conf import settings

    query = CategoriesModel.objects.filter(is_deleted=False, shop__isnull=False, match__id__isnull=True)
    categories = query.all()
    model_path = os.path.join(settings.BASE_DIR, 'models_ai', 'main_category.pkl')
    model = joblib.load(model_path)
    for category in categories:
        products = ProductModel.objects.filter(category=category).all()
        count = {}
        for product in products:

            name = f'{category.name} - {product.name}'
            predicted_category = model.predict([name])[0]
            try:
                count[predicted_category].append(product.id)
            except:
                count[predicted_category] = [product.id]
        if count:
            max_key = max(count, key=lambda k: len(count[k]))
            print(f"{category.name} : {max_key}")
            is_match_cat = CategoriesModel.objects.filter(name__iexact=max_key, parent__isnull=True,
                                                          shop__isnull=True).first()
            category.match = is_match_cat
            category.save()


def shop_category_match_fix(product, category):
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


def predict_fix_unicode(predict):
    if predict == 'gıda & içecek':
        predict = 'gıda & İçecek'
    if predict == 'içecek hazırlama':
        predict = 'İçecek hazırlama'
    if predict == 'araç içi aksesuarı':
        predict = 'araç İçi aksesuarı'
    if predict == 'araç içi telefon tutucu':
        predict = 'araç İçi telefon tutucu'
    if predict == 'dolap içi düzenleyici':
        predict = 'dolap İçi düzenleyici'
    if predict == 'sinek ilacı ve kovucu':
        predict = 'sinek İlacı ve kovucu'

    return predict

@shared_task
def category_set_brand(datas):
    from brands.models import BrandModel
    from categories.models import CategoriesModel

    for data in datas:
        if 'brand_id' in data:
            brand = BrandModel.objects.get(pk=data['brand_id'])
            category = CategoriesModel.objects.get(pk=data['category_id'])
            is_exist = category.brands.filter(id=brand.id).first()
            if is_exist is None:
                category.brands.add(brand)

    return 'category_set_brand ok!'

@shared_task
def remove_dublicate_category():
    from categories.models import CategoriesModel
    shop_categories = CategoriesModel.objects.filter(match__isnull=True, shop__isnull=False, is_deleted=False).all()
    for cat in shop_categories:
        deleteds = CategoriesModel.objects.filter(name=cat.name, shop=cat.shop, match__isnull=True, shop__isnull=False, is_deleted=False).all()
        if len(deleteds)>1:
            print(f"{cat.name} : {deleteds[0].name}")
            for del_ in deleteds:
                if del_.id != cat.id:
                    print(f"{del_.name} silindi")
                    del_.is_deleted = True
                    del_.save()
@shared_task
def ai_product_category_fix():
    from products.models import ProductModel

    from categories.models import CategoriesModel
    import joblib
    import os

    from django.conf import settings
    from django.core.paginator import Paginator

    if_not_check_categories = []
    if_not_check_products = []
    shop_categories = CategoriesModel.objects.filter(match__isnull=True, shop__isnull=False).exclude(shop=1).iterator()
    for category in shop_categories:
        print(category.id)
        is_match_category = CategoriesModel.objects.filter(shop__isnull=True, name__iexact=category.name).first()
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

            print(f'{category.name} - {category.id} - {query.count()}')
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
                    category1 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True).first()
                    model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category1.id}_category.pkl')
                    model = joblib.load(model_path)
                    predict = model.predict([product_name])[0]
                    predict = predict_fix_unicode(predict)
                    category2 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True).first()

                    # alt kategorisi yok ise
                    if category2 is not None:
                        is_exist = CategoriesModel.objects.filter(parent=category2.id, is_deleted=False).exists()
                        if not is_exist:
                            category_, product = shop_category_match_fix(product, category2)
                            try:
                                predict_pool[category_.id].append(product.id)
                            except Exception as e:
                                predict_pool[category_.id] = [product.id]

                        else:
                            model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category2.id}_category.pkl')
                            model = joblib.load(model_path)
                            predict = model.predict([product_name])[0]
                            predict = predict_fix_unicode(predict)
                            category3 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True).first()

                            #alt kategorisi yok ise
                            if category3 is not None:
                                is_exist = CategoriesModel.objects.filter(parent=category3.id, is_deleted=False).exists()
                                if not is_exist:
                                    category_, product = shop_category_match_fix(product, category3)
                                    try:
                                        predict_pool[category_.id].append(product.id)
                                    except Exception as e:
                                        predict_pool[category_.id] = [product.id]
                                else:
                                    model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category3.id}_category.pkl')
                                    model = joblib.load(model_path)
                                    predict = model.predict([product_name])[0]
                                    predict = predict_fix_unicode(predict)
                                    category4 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True).first()
                                    if category4 is not None:
                                        # alt kategorisi yok ise
                                        is_exist = CategoriesModel.objects.filter(parent=category4.id, is_deleted=False).exists()
                                        if not is_exist:
                                            category_, product = shop_category_match_fix(product, category4)
                                            try:
                                                predict_pool[category_.id].append(product.id)
                                            except Exception as e:
                                                predict_pool[category_.id] = [product.id]
                                        else:
                                            model_path = os.path.join(settings.BASE_DIR, 'models_ai', f'{category4.id}_category.pkl')
                                            model = joblib.load(model_path)
                                            predict = model.predict([product_name])[0]
                                            predict = predict_fix_unicode(predict)
                                            category5 = CategoriesModel.objects.filter(name__iexact=predict, shop__isnull=True).first()
                                            # alt kategorisi yok ise
                                            if category5 is not None:
                                                is_exist = CategoriesModel.objects.filter(parent=category5.id, is_deleted=False).exists()
                                                if not is_exist:
                                                    category_, product = shop_category_match_fix(product, category5)
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


