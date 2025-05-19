import io
import os
import traceback

from itertools import product
import inspect
import requests
import csv
import json
import hashlib
import time
from decimal import Decimal

from datetime import timedelta, datetime

from elasticsearch.helpers import bulk
from elasticsearch_dsl.connections import get_connection

from django.utils import timezone
from django.utils.text import slugify
from django.db.models import Q
from django.db import transaction
from django.db import connection

from celery import shared_task, current_app
from django.core.paginator import Paginator
from utils.utils import calculate_file_hash

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)


@shared_task
def upload_images(url, product_id=None, link=None):
    from utils.s3 import S3
    from attachment.models import AttachmentModel
    from products.models import ProductModel
    from synchronize_error.models import SynchronizeModel

    if product_id is not None:
        product = ProductModel.objects.filter(id=product_id).first()

    if link is not None:
        product = ProductModel.objects.filter(link=link).first()

    if product is None:
        is_data = SynchronizeModel.objects.filter(data=url, product=product_id).exists()
        if not is_data:
            SynchronizeModel.objects.create(error='Ürün bulunamadı', product=product_id, data=url, script_file='upload_images')
        return 'Ürün daha eklenmemiş'

    instance = AttachmentModel.objects.filter(is_deleted=False,
                                              original_file_url=url).first()
    if instance is None:
        s3 = S3()
        if url is None:
            return False
        try:
            image, filename, resized_file_size = s3.download_and_resize_image(url)
            today = timezone.now().date()
            upload_url = s3.send_file(image, filename, today)
            instance = AttachmentModel.objects.create(name=filename,
                                                      original_name=filename,
                                                      original_file_url=url,
                                                      thumb_file_url=upload_url)
            if product.image is None:
                product.gallery.add(instance)
            else:
                is_exist = product.gallery.filter(id=product.image.id).exists()
                if is_exist is None:
                    product.gallery.add(instance)
            img = AttachmentModel.objects.filter(id=instance.id).first()
            product.image = img
            product.save()
        except Exception as e:
            print('*****errror*****')
            print(product)
            print(product_id)
            if product is not None:
                shop = product.shop
            else:
                shop = None
            error_details = traceback.format_exc()
            SynchronizeModel.objects.create(error=error_details, data=url, shop=shop, script_file='upload_images' )
            return False
    else:
        if product is not None:
            #img = AttachmentModel.objects.filter(id=instance.id).first()
            product.image = instance
            product.save()
    return True

@shared_task
def elasticsearch_bulk(datas):
    from products.serializers import ProductsElasticSerializer
    from products.documents import ProductDocument
    from products.models import ProductModel
    action = []
    es = get_connection()
    for instance in datas:
        product = ProductModel.objects.filter(link=instance['link']).first()
        if product is not None:
            serializer = ProductsElasticSerializer(product)
            act = {
                "_op_type": "update",
                "_index": ProductDocument._index._name,
                "_id": product.id,
                "doc": serializer.data,
                "doc_as_upsert": True,
            }
            action.append(act)
    bulk(es, action)

@shared_task
def price_history(old_price, price, shop_id, sub_merchant_id, product_id):
    from products.models import ProductPriceModel, ProductModel
    from shops.models import ShopModel,SubMerchantModel

    if old_price is None:
        old_price = ProductModel.objects.filter(id=product_id).values_list('price', flat=True).first()

    print(f'{str(old_price)} == {str(price)}')
    old_price = float(old_price)
    price_float = float(price)
    print(f'{str(old_price)} == {str(price_float)}')

    if old_price != price_float:
        product = ProductModel.objects.get(pk=product_id)
        shop = ShopModel.objects.get(pk=shop_id)
        if sub_merchant_id is not None:
            sub_merchant = SubMerchantModel.objects.get(pk=sub_merchant_id)
        else:
            sub_merchant = None
        dt = ProductPriceModel.objects.create(
            price=price,  # Replace with the actual price
            shop=shop,  # Replace with the actual shop price if necessary
            sub_merchant_shop=sub_merchant
        )

        product.price_history.add(dt)

    return 'OK'


@shared_task
def resize_again():
    from utils.s3 import S3
    from attachment.models import AttachmentModel
    page_size = 100

    images_query = AttachmentModel.objects.filter(is_deleted=False)
    images_count = images_query.count()

    for i in range(images_count / page_size):
        images = images_query.all()[i:page_size]
        s3 = S3()
        for image in images:
            image_resource, filename, resized_file_size = s3.download_and_resize_image(image.original_file_url)
            folder = image.thumb_file_url.split('/')
            s3.send_file(image_resource, image.name, folder[4])
            print(f'ok {image.name}')


def check_category(product_category_name, shop_instance, brand):
    from categories.models import CategoriesModel
    is_category = CategoriesModel.objects.filter(name=product_category_name, is_deleted=False,
                                                 shop__isnull=True).first()
    if is_category is None:
        is_category = CategoriesModel.objects.filter(name=product_category_name,
                                                     is_deleted=False,
                                                     shop=shop_instance).first()
        if is_category is None:
            is_category = CategoriesModel.objects.create(name=product_category_name, shop=shop_instance)
        else:
            if is_category.match is not None:
                is_category = CategoriesModel.objects.get(pk=is_category.match)

    #category markayı eşitle
    is_category.brands.add(brand)

    return is_category


def save_product(data, product_image, shop_instance, sub_merchant):
    from products.serializers import ProductsSerializer
    from synchronize_error.models import SynchronizeModel
    from products.models import ProductModel, ProductPriceModel

    product_instance = ProductModel.objects.filter(is_deleted=False, link=data['link']).first()

    if product_instance is None:
        print('adding new product')

        serializer = ProductsSerializer(data=data)
        old_price = 0
    else:
        print('update existing product')
        serializer = ProductsSerializer(product_instance, data=data)
        old_price = product_instance.price
    try:
        serializer.is_valid(raise_exception=True)

        product_instance = serializer.save()
        print('image task')
        upload_images(product_image, product_instance.id)
        if str(old_price) != str(data['price']):
            dt = ProductPriceModel.objects.create(
                price=data['price'],  # Replace with the actual price
                shop=shop_instance,  # Replace with the actual shop price if necessary
                sub_merchant_shop=sub_merchant
            )
            product_instance.price_history.add(dt)
    except Exception as e:
        print(e)
        error_details = traceback.format_exc()
        SynchronizeModel(shop=shop_instance, error=str(error_details), data=json.dumps(data)).save()


def hash_check(url, content_stream):
    from attachment.models import FileMetadataModel
    previous_file = FileMetadataModel.objects.filter(file_url=url, is_deleted=False).first()
    if previous_file is not None:
        is_change, old_hash = compare_file_hashes(content_stream, previous_file.file_hash)
    else:
        is_change, old_hash = compare_file_hashes(content_stream, '')

    return is_change, old_hash


def download_url(url, save=False):
    response = requests.get(url)
    response.raise_for_status()
    file_size_bytes = len(response.content)
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"Downloaded file size: {file_size_mb} bytes")
    data_content = response.content
    content_stream = io.BytesIO(data_content)
    if save:
        save_path = 'download.xml'
        with open(save_path, 'wb') as file:
            file.write(data_content)
        print(f"File saved to {save_path}")
    # file = 'Fiyator.csv'
    # with open(file, 'rb') as f:
    #     # Read the file content as bytes
    #     data_content = f.read()
    #
    #     # Get the size of the file in bytes
    #     file_size_bytes = os.path.getsize(file)
    #
    #     # Calculate file size in megabytes (MB)
    #     file_size_mb = file_size_bytes / (1024 * 1024)  # 1 MB = 1024 * 1024 bytes
    #
    #     # Get a ShopModel instance (replace 'pk=1' with the appropriate query)
    #     shop_instance = ShopModel.objects.get(pk=1)
    #
    #     # Create a BytesIO stream with the file content
    #     content_stream = io.BytesIO(data_content)

    return data_content, content_stream, file_size_bytes


def ptt_products():
    import xml.etree.ElementTree as ET
    from attachment.models import FileMetadataModel
    from shops.models import ShopModel
    url = os.getenv('PTT_URl')
    data_content, content_stream, file_size_bytes = download_url(url)
    shop_instance = ShopModel.objects.get(pk=3)

    is_change, old_hash = hash_check(url, content_stream)
    if is_change:
        return False

    root = ET.fromstring(data_content)
    for merchant_item in root.findall('./channel/product'):
        product_category_name = merchant_item.find('product_type').text
        try:
            brand = merchant_item.find('brand').text
        except:
            brand = 'Diğer'
        product_name = merchant_item.find('title').text
        product_link = merchant_item.find('link').text
        stock_status = merchant_item.find('stock').text
        product_seller = 'PttAVM'
        product_code = ''
        product_barcode = ''
        product_sku = ''
        product_price = merchant_item.find('price').text
        product_cargo_price = 0
        product_tax = 0
        product_slug = slugify(product_name)
        product_image = merchant_item.find('image_link').text
        print(product_image)
        if product_name is not None or product_name != '':
            # brand varsa al yoksa ekle
            brand = check_brand(brand)
            # submerchant varsa al yoksa ekle
            sub_merchant = check_submerchant(product_seller, shop_instance)
            # category varsa al yoksa ekle
            is_category = check_category(product_category_name, shop_instance, brand)

            data = {
                "category": is_category.id,
                "brand": brand.id,
                "name": product_name,
                "slug": product_slug,
                "link": product_link,
                "model_code": product_code,
                "barcode": product_barcode,
                "sku": product_sku,
                "price": product_price,
                "cargo_price": product_cargo_price,
                "kdv": product_tax,
                "shop": shop_instance.id,
                "sub_merchant_shop": sub_merchant.id
            }
            print(data)
            save_product(data, product_image, shop_instance, sub_merchant)
    file_meta_instance = FileMetadataModel(file_name='Ptt', file_url=url, file_hash=old_hash,
                                           file_size_byte=file_size_bytes)
    file_meta_instance.save()


def teknosa_products():
    import xml.etree.ElementTree as ET
    from attachment.models import FileMetadataModel
    from shops.models import ShopModel
    url = os.getenv('TEKNOSA_URL')
    data_content, content_stream, file_size_bytes = download_url(url)
    shop_instance = ShopModel.objects.get(pk=2)

    is_change, old_hash = hash_check(url, content_stream)
    if is_change:
        return False

    root = ET.fromstring(data_content)
    ns = {'cimri': 'http://www.cimri.com/schema/merchant/upload'}
    for merchant_item in root.findall('cimri:MerchantItem', ns):
        product_category_name = merchant_item.find('cimri:merchantItemCategoryName', ns).text
        try:
            brand = merchant_item.find('cimri:brand', ns).text
        except:
            brand = 'Diğer'

        product_name = merchant_item.find('cimri:itemTitle', ns).text
        product_link = merchant_item.find('cimri:itemUrl', ns).text
        stock_status = merchant_item.find('cimri:stockStatus', ns).text
        product_seller = merchant_item.find('cimri:merchantName', ns).text
        product_code = merchant_item.find('cimri:merchantItemId', ns).text
        product_barcode = merchant_item.find('cimri:ean', ns).text
        product_sku = ''
        product_price = merchant_item.find('cimri:priceEft', ns).text
        product_cargo_price = merchant_item.find('cimri:shippingFee', ns).text
        product_tax = 0
        product_slug = slugify(product_name)
        product_image = merchant_item.find('cimri:itemImageUrl', ns).text
        if product_name is not None or product_name != '':
            # brand varsa al yoksa ekle
            brand = check_brand(brand)
            # submerchant varsa al yoksa ekle
            sub_merchant = check_submerchant(product_seller, shop_instance)
            # category varsa al yoksa ekle
            is_category = check_category(product_category_name, shop_instance, brand)

            data = {
                "category": is_category.id,
                "brand": brand.id,
                "name": product_name,
                "slug": product_slug,
                "link": product_link,
                "model_code": product_code,
                "barcode": product_barcode,
                "sku": product_sku,
                "price": product_price,
                "cargo_price": product_cargo_price,
                "kdv": product_tax,
                "shop": shop_instance.id,
                "sub_merchant_shop": sub_merchant.id
            }
            print(data)
            save_product(data, product_image, shop_instance, sub_merchant)
    file_meta_instance = FileMetadataModel(file_name='Teknosa', file_url=url, file_hash=old_hash,
                                           file_size_byte=file_size_bytes)
    file_meta_instance.save()


def trendyol_products(is_change=None):
    from attachment.models import FileMetadataModel
    from shops.models import ShopModel
    from synchronize_error.models import SynchronizeModel

    url = os.getenv('TRENDYOL_URL')
    data_content, content_stream, file_size_bytes = download_url(url)
    shop_instance = ShopModel.objects.get(pk=1)

    is_change, old_hash = hash_check(url, content_stream)
    if is_change:
        return False

    print(f"File Hash: {is_change} status")

    # Create an in-memory file-like object for reading CSV data
    csv_data = data_content.decode('utf-8').splitlines()
    # Process CSV data row by row
    csv_reader = csv.reader(csv_data)
    next(csv_reader)
    i = 0
    for row in csv_reader:
        print(row)
        product_name = row[0]
        product_slug = slugify(product_name)
        product_link = row[1]
        product_image = row[2]
        product_item_condition = row[3]
        product_code = row[4]
        product_sku = row[5]
        product_barcode = row[6]
        product_item_number = row[7]
        product_listing_id = row[8]
        product_gtin_13 = row[9]
        product_color = row[10]
        product_has_stock = row[11]
        product_price = row[12]
        product_tax = row[13]
        product_brand = row[14]
        product_seller = row[15]
        product_category_id = row[16]
        product_category_name = row[17]
        product_category_hierarchy = row[18]
        product_size = row[19]
        product_gender = row[20]
        product_cargo_price = row[21]
        product_is_free_cargo = row[22]
        product_merchant_id = row[23]
        product_content_id = row[24]
        product_boutique_id = row[25]
        product_filter_6m_trx = row[26]
        i = i + 1
        print(i)
        print(product_name)
        print('***************')
        # Example: Save each row to a database model
        # Assuming you have a Django model named MyModel with fields matching CSV columns
        # MyModel.objects.create(field1=row[0], field2=row[1], ...)

        if product_name is not None or product_name != '':
            try:
                #brand varsa al yoksa ekle
                brand = check_brand(product_brand)
                #submerchant varsa al yoksa ekle
                sub_merchant = check_submerchant(product_seller, shop_instance, product_merchant_id)
                #category varsa al yoksa ekle
                is_category = check_category(product_category_name, shop_instance, brand)

                data = {
                    "category": is_category.id,
                    "brand": brand.id,
                    "name": product_name,
                    "slug": product_slug,
                    "link": product_link,
                    "model_code": product_code,
                    "barcode": product_barcode,
                    "sku": product_sku,
                    "price": product_price,
                    "cargo_price": product_cargo_price,
                    "kdv": product_tax,
                    "shop": shop_instance.id,
                    "sub_merchant_shop": sub_merchant.id
                }

                save_product(data, product_image, shop_instance, sub_merchant)
            except Exception as e:
                error_details = traceback.format_exc()
                SynchronizeModel(shop=shop_instance, error=str(error_details), data=json.dumps(data)).save()

    file_meta_instance = FileMetadataModel(file_name='Trendyol', file_url=url, file_hash=old_hash,
                                           file_size_byte=file_size_bytes)
    file_meta_instance.save()





def compare_file_hashes(file_path, previous_hash):
    """Compare the hash of a file with a previously stored hash."""
    current_hash = calculate_file_hash(file_path)
    return (current_hash == previous_hash), current_hash


def check_brand(product_brand):
    from brands.models import BrandModel
    brand = BrandModel.objects.filter(name=product_brand).first()

    if brand is None:
        brand = BrandModel(name=product_brand)
        brand.save()
    return brand

def parent_match(parent_id):
    from products.models import ProductModel
    query = 'SELECT * FROM products_match WHERE to_productmodel_id=%s'
    params = [parent_id]
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row is not None:
            return row[1]


def check_submerchant(product_seller, shop_instance, product_merchant_id=None):
    from shops.models import SubMerchantModel
    from shops.serializers import SubMerchantSerializer

    data = {
        'name': product_seller,
        'merchant': product_merchant_id,
        'shop': shop_instance.id,
    }

    is_sub_merhant = SubMerchantModel.objects.filter(name=product_seller, is_deleted=False,
                                                     shop=shop_instance).first()
    if is_sub_merhant is None:
        serializer = SubMerchantSerializer(data=data)
    else:
        serializer = SubMerchantSerializer(is_sub_merhant, data=data)
    serializer.is_valid(raise_exception=True)
    sub_merchant = serializer.save()
    return sub_merchant


@shared_task
def trendyol():
    trendyol_products()


@shared_task
def teknosa():
    teknosa_products()


@shared_task
def ptt_avm():
    ptt_products()


@shared_task
def category_name_like_match(category_id=None):
    from utils.chatgpt import ChatGptApi
    from categories.models import CategoriesModel
    if category_id is not None:
        categories = CategoriesModel.objects.filter(Q(shop__isnull=False),
                                                    is_deleted=False,
                                                    match__isnull=True,
                                                    id=category_id).all()
    else:
        categories = CategoriesModel.objects.filter(Q(shop__isnull=False),
                                                    is_deleted=False,
                                                    match__isnull=True).all()
    for category in categories:
        print(f'Bulunacak kategori {category.name}')
        cat = CategoriesModel.objects.filter(name__iexact=category.name, shop__isnull=True).first()

        if cat is not None:
            print(f'Eşleşen kategori {cat.name}')
            category.match = cat
            category.save()


@shared_task
def category_match(category_id=None):
    from utils.chatgpt import ChatGptApi
    from categories.models import CategoriesModel
    if category_id is not None:
        categories = CategoriesModel.objects.filter(Q(shop__isnull=False),
                                                    is_deleted=False,
                                                    match__isnull=True,
                                                    id=category_id).all()
    else:
        categories = CategoriesModel.objects.filter(Q(shop__isnull=False),
                                                    is_deleted=False,
                                                    match__isnull=True).all()
    chat = ChatGptApi('')
    for category in categories:
        #trendyol kategorisi değilse eşleştir.
        if category.shop.id != 1:
            print(f'Bulunacak kategori {category.name}')
            chat.upload_categories_to_chatgpt(category.id, category.name)

@shared_task
def product_name_likes():
    from products.models import ProductModel

    #TODO tüm ürünleri al silinmemiş ve eşleşmemişler
    query = ProductModel.objects.filter(is_match=False, is_deleted=False, match__isnull=True)
    paginator = Paginator(query, 10)
    total_pages = paginator.num_pages
    print(f"Toplam sayfa sayısı: {total_pages}")

    for i in range(0, total_pages):
        products = paginator.get_page(i)
        for product in products:

            #TODO bu ürüne benzer aynı isimde ürün varmı
            sames = (ProductModel.objects.filter(name__iexact=product.name,
                                                 is_deleted=False,
                                                 match__isnull=True,
                                                 is_match=False).exclude(id=product.id).all())
            for same in sames:
                print(f'{str(product.id)} : {str(same.id)} - {same.name}')
                same.is_match = True
                same.save()
                product.match.add(same.id)


@shared_task
def product_name_likes_fuzznize():

    from products.models import ProductModel
    from tasks.models import TasksModel
    from products.documents import ProductDocument

    limit = 10
    while True:
        total = ProductModel.objects.filter(is_match=False, match__isnull=True, is_deleted=False).count()
        total_pages = round(total / limit) + 1

        task = TasksModel.objects.filter(name='product_name_likes_fuzznize', status=0).first()
        if not task:
            task = TasksModel.objects.create(name='product_name_likes_fuzznize', page=0, status=0, total_page=total_pages)

        if total_pages < (task.page/limit):
            task.status=1
            task.save()

        #TODO Tüm ürünler al yayında olan ve matchleşmemiş
        task.page = task.page + limit
        task.save()
        products = ProductModel.objects.filter(is_match=False, match__isnull=True, is_deleted=False)[task.page:(task.page+limit)]

        for product in products:
            if product.is_match:
                break
            if product.match.exists():
                break
            start_time = time.time()
            #TODO bir ürünün ismini al ve elasticsearch üzerinde benzerlerini getir.
            if product.name is not None:
                search = ProductDocument.search().query("multi_match", query=product.name, fields=['name^5'])
                response = search.execute()
                matches_to_create = []
                for hit in response:
                    item = hit.to_dict()
                    item['score'] = hit.meta.score
                    if hit.meta.score > 200:
                        #print(hit.meta.score)
                        #TODO buldugu ürün kendisi değilse.
                        if item['id'] != product.id:
                            # TODO buldugu ürün ile aradığım ürünün marka ismi aynımı
                            #if item['brand']['name'].lower() == product.brand.name.lower():
                            #if item['price'] == product.price:
                            # print(item['name'] + '==' + product.name)
                            # print(str(item['id']) + '==' + str(product.id))
                            prd = ProductModel.objects.filter(id=item['id']).first()
                            #TODO buldugumuz ürün herhangi bir seyin altında matchleşmişmi
                            if prd is not None:
                                if prd.is_match:
                                    parent_id = parent_match(prd.id)
                                    is_match = ProductModel.objects.filter(id=parent_id).exclude(id=prd.id).first()
                                    product.is_match = True
                                    product.save()
                                    if is_match is not None:
                                        is_match.match.add(product)
                                else:
                                    #TODO buldugumuz ürünün altında matchleşmiş ürün varmı
                                    if prd.match.exists():
                                        product.is_match = True
                                        product.save()
                                        prd.match.add(product)
                                    else:
                                        #TODO ikli üründe eşleşmemişse bulunan ürünü altına at.
                                        prd.is_match = True
                                        prd.save()
                                        product.match.add(prd)
                end_time = time.time()
                print(f"{product.id} Fonksiyonun çalışma süresi: {end_time - start_time:.6f} saniye")


@shared_task
def discounted_product():
    from django.db.models import Count
    from products.models import ProductModel, ProductDiscountModel

    # Önce eski kayıtları temizle
    ProductDiscountModel.objects.all().delete()

    # En az 2 fiyat geçmişi olan ve en son güncellenen ürünleri seç
    query = ProductModel.objects.filter(is_deleted=False).annotate(
        fiyat_sayisi=Count('price_history')
    ).filter(
        fiyat_sayisi__gt=1
    ).order_by('-updated_at')  # En son güncellenenler önce gelsin

    paginator = Paginator(query, 100)  # Sayfalama işlemi
    total_pages = paginator.num_pages
    print(f"Toplam sayfa sayısı: {total_pages}")

    fiyat_dusen_urunler = []

    # Sayfalı işlem yap
    for i in range(0, total_pages):
        page = paginator.get_page(i)

        for product in page:
            # Fiyat geçmişini sıralı al
            all_price = product.price_history.order_by('-created_at')
            if all_price.count() > 1 and product.price < all_price[1].price:
                fiyat_dusen_urunler.append(product)

            # Eğer 100 ürün ise durdur
            if len(fiyat_dusen_urunler) >= 100:
                break

        if len(fiyat_dusen_urunler) >= 100:
            break

    # Sadece ilk 100 ürünü kaydet
    for product in fiyat_dusen_urunler[:100]:
        ProductDiscountModel.objects.create(product=product)

    return f"{len(fiyat_dusen_urunler[:100])} fiyatı düşen ürün eklendi"



@shared_task
def old_wait_product():
    from products.models import ProductModel
    now = timezone.now()
    two_days_ago = now - timedelta(days=4)
    query = ProductModel.objects.filter(is_deleted=False, updated_at__lt=two_days_ago)
    paginator = Paginator(query, 100)
    total_pages = paginator.num_pages
    for i in range(0, total_pages+1):
        products = paginator.get_page(i)
        for product in products:
            product.is_deleted = True
            product.save()

@shared_task
def youtube_video():
    from products.models import ProductModel
    from utils.youtube_api import Youtube
    from tasks.models import TasksModel, Status

    task = TasksModel.objects.filter(
        name='youtube_video',
        status=Status.PROGRESS,
        is_deleted=False
    ).first()
    
    if not task:
        task = TasksModel.objects.create(name='youtube_video')

    youtube = Youtube()
    query = ProductModel.objects.filter(is_deleted=False, video_url__isnull=True)
    paginator = Paginator(query, 100)
    
    if task.total_page == 0:
        task.total_page = paginator.num_pages
        task.save()

    for i in range(task.page, task.total_page + 1):
        try:
            products = paginator.get_page(i)
            for product in products:
                try:
                    video = youtube.search(product.name)
                    if video:
                        product.video_url = video
                        product.save()
                except Exception as e:
                    print(f"Error processing product {product.id}: {str(e)}")
                    continue
            
            task.page = i
            task.save()
            
        except Exception as e:
            print(f"Error processing page {i}: {str(e)}")
            task.status = Status.ERROR
            task.save()
            return False

    task.status = Status.COMPLETE 
    task.save()
    return True


def create_price_change_notification(alarm, current_price, alarm_price):
    from users.models import NotificationModel
    
    if current_price > alarm_price:
        title = "Fiyat Artışı"
        content = f'Takip ettiğiniz {alarm.product.name} ürününün fiyatı {alarm_price} TL\'den {current_price} TL\'ye yükseldi.'
    else:
        title = "Fiyat Düşüşü"
        content = f'Takip ettiğiniz {alarm.product.name} ürününün fiyatı {alarm_price} TL\'den {current_price} TL\'ye düştü.'

    try:
        NotificationModel.objects.create(
            user=alarm.user,
            subject="Fiyat Değişikliği",
            title=title, 
            content=content,
            status=False,
            is_deleted=False
        )
    except Exception as e:
        print(f"Error in create_price_change_notification: {str(e)}")

@shared_task
def check_price_changes():
    """
    Check price changes for all active price alarms and send notifications
    """
    from .models import ProductPriceAlarmModel
    from mail.models import MailModel

    alarms = ProductPriceAlarmModel.objects.filter(is_deleted=False)
    for alarm in alarms:
        # current_price ve alarm_price'ı float olarak tanımla
        current_price = float(alarm.product.price) if alarm.product.price is not None else 0.0
        alarm_price = float(alarm.price) if alarm.price is not None else 0.0
        
        # Eğer fiyat değişikliği varsa
        if current_price != alarm_price:
            if current_price > alarm_price:
                mail_type = 3
                subject = 'Fiyat Artışı Bildirimi'
                message = f'Takip ettiğiniz {alarm.product.name} ürününün fiyatı {alarm_price} TL\'den {current_price} TL\'ye yükseldi.'
            else:
                mail_type = 4
                subject = 'Fiyat Düşüşü Bildirimi'
                message = f'Takip ettiğiniz {alarm.product.name} ürününün fiyatı {alarm_price} TL\'den {current_price} TL\'ye düştü.'

            # MailModel oluşturma sırasında float değerler kullan
            try:
                data = {
                    'product_name': str(alarm.product.name),
                    'old_price': float(alarm_price),  # Decimal -> float
                    'new_price': float(current_price),  # Decimal -> float
                    'product_url': f"{os.getenv('FRONTEND_URI')}/product-detail/{alarm.product.id}/{alarm.product.slug}",
                    'user_name': f"{alarm.user.first_name or ''} {alarm.user.last_name or ''}".strip() or 'Değerli Üyemiz'
                }
                
                MailModel.objects.create(
                    user=alarm.user,
                    to=alarm.user.email,
                    subject=subject,
                    content=json.dumps(data),
                    mail_type=mail_type,
                    status=0,
                    try_count=0,
                    is_deleted=False
                )

                # Create notification
                create_price_change_notification(alarm, current_price, alarm_price)

                # Alarm fiyatını güncelle
                alarm.price = current_price
                alarm.save()
            except Exception as e:
                print(f"Error in check_price_changes: {str(e)}")
                continue

    return "Price changes checked successfully"

@shared_task
def clean_duplicate_brands():
    from django.db import transaction
    from django.db.models import Count
    from brands.models import BrandModel
    from products.models import ProductModel

    # Önce tüm markaları küçük harfe çevirip grupla
    from django.db.models.functions import Lower
    duplicate_brands = BrandModel.objects.annotate(
        name_lower=Lower('name')
    ).values('name_lower').annotate(
        count=Count('id')
    ).filter(count__gt=1)

    for duplicate in duplicate_brands:
        brand_name = duplicate['name_lower']
        # Her grup için markaları oluşturulma tarihine göre sırala
        similar_brands = list(BrandModel.objects.filter(
            name__iexact=brand_name
        ).order_by('created_at'))

        if not similar_brands:
            continue

        main_brand = similar_brands[0]
        duplicates = similar_brands[1:]

        try:
            with transaction.atomic():
                for duplicate_brand in duplicates:
                    # Ürünleri ana markaya yönlendir
                    ProductModel.objects.filter(brand=duplicate_brand).update(brand=main_brand)
                    
                    # Duplicate markayı sil
                    duplicate_brand.is_deleted = True
                    duplicate_brand.save()

        except Exception as e:
            print(f"{main_brand.name} markasını işlerken hata oluştu: {str(e)}")
            continue

    return "Marka temizleme işlemi tamamlandı"

@shared_task
def update_shop_elasticsearch_index(shop_id):
    """
    Mağaza aktif/pasif durumu değiştiğinde Elasticsearch indeksini doğrudan günceller.
    Bu task asenkron olarak çalışır ve admin panelde yavaşlığa neden olmayacak.
    """
    from products.documents import ProductDocument
    from products.models import ProductModel
    from elasticsearch_dsl import Search
    from django.conf import settings
    
    try:
        # Elasticsearch bağlantısı
        es = get_connection()
        
        # Mağaza bilgileri
        from shops.models import ShopModel
        shop = ShopModel.objects.get(id=shop_id)

        # Sadece mağazanın aktiflik durumunu ürünlerin shop.is_active alanına yansıt
        # Update by query kullanarak mağazanın aktiflik durumunu güncelle
        update_query = {
            "script": {
                "source": "ctx._source.shop.is_active = params.is_active",
                "lang": "painless",
                "params": {
                    "is_active": shop.is_active
                }
            },
            "query": {
                "term": {
                    "shop_id": shop_id
                }
            }
        }
        
        # Elasticsearch'teki ürünleri güncelle
        result = es.update_by_query(index=ProductDocument._index._name, 
                                     body=update_query,
                                     conflicts="proceed")
        
        updated_count = result.get('updated', 0)
        print(f"Shop ID {shop_id} için {updated_count} ürünün görünürlük durumu güncellendi. Mağaza durumu: {'Aktif' if shop.is_active else 'Pasif'}")
        
    except Exception as e:
        print(f"Elasticsearch güncelleme hatası: {str(e)}")
        import traceback
        traceback.print_exc()