import requests
import io
import re
import os
import sys
import json
import cloudscraper

from tqdm import tqdm

from django.utils import timezone
from urllib.parse import urlparse

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from selenium.webdriver.chrome.service import Service as ChromeService
from django.utils.text import slugify
from django.core.cache import cache

from products.serializers import ProductsSerializer
from shops.models import SubMerchantModel, ShopModel
from shops.serializers import SubMerchantSerializer
from products.models import ProductModel
from synchronize_error.models import SynchronizeModel, SynchronizeUrlsModel
from utils import utils
from utils.parse_html import ParseHtml

from brands.models import BrandModel
from categories.models import CategoriesModel
from products.tasks import upload_images, elasticsearch_bulk
from categories.tasks import category_set_brand
from specs.tasks import spec_progress

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import unquote,urlparse,urlunparse
from bs4 import BeautifulSoup
from products.tasks import price_history, upload_images

#from transformers import BertTokenizerFast, BertForTokenClassification, pipeline
# model = BertForTokenClassification.from_pretrained("./results")
# tokenizer = BertTokenizerFast.from_pretrained("./results")
# nlp = pipeline("token-classification", model=model, tokenizer=tokenizer,aggregation_strategy="simple")

class ProductSave:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept': 'text/html,applicatiosn/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-GB;q=0.8,en;q=0.7,en-US;q=0.6',
            'Connection': 'keep-alive'
        }
        self.cache_brands = cache.get('all_brands')
        self.cache_categories = cache.get('all_categories')
        self.cache_sub_merchant = cache.get('all_sub_merchant')
        self.parse_html = ParseHtml()

    def driver_self(self, remote=False):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        if remote:
            selenium_server_url = os.getenv('SELENIUM_URI')
            driver_ = webdriver.Remote(
                command_executor=selenium_server_url,
                options=chrome_options  # Use ChromeOptions or appropriate options class
            )
        else:
            driver_ = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

        driver_.set_page_load_timeout(30)
        return driver_

    def price_fix(self, price):
        price = str(price)
        price = (((price.replace('İndirimli fiyat','')
                 .replace('\r','')
                 .replace('\t',''))
                 .replace('%20',''))
                 .replace('indirim','')
                 .replace('İndirimli', '')
                 .replace('�r�n Yorumlar�', '')
                 .replace('Satış Fiyatı', '')
                 .replace('Fiyat', '')
                 .replace('(KDV Dahil)', '')
                 .replace('#', '')
                 .replace(':', '')
                 .replace('indirimli fiyat', '')
                 .replace('tr', '')
                 .replace('( Kdv Dahil)', ''))
        price = re.sub(r"[^\d.,]", "", price)
        price = price.replace('\n', '')
        if all(char in price for char in ['.', ',']):
            ord1 = price.index(',')
            ord2 = price.index('.')
            if ord1 > ord2:
                price = price.replace('.', '')
            else:
                price = price.replace(',', '')

        price = price.replace('TL', '')
        if price == '':
            return 0
        if price is None:
            return 0
        price = price.replace(' ', '').replace('TRY', '').replace('₺', '').replace('Fiyat:', '')
        if '.' in price:
            price_bol = price.split('.')
            if len(price_bol) < 3:
                if len(price_bol[1]) > 2:
                    if ',' not in price:
                        price = str(price)
                        #price = str(price).replace('.', ',')
                else:
                    price = price.replace('.', ',')

        price = price.replace('.', '').replace(',', '.')
        if price is not None:
            if '.' in str(price):
                price_split = str(price).split('.')
                if len(price_split[1]) > 4:
                    price = re.search(r'\b\d+(\.\d{1,2})?\b', price)
                    if price is None:
                        return price

                    try:
                        price = float(price)
                    except:
                        price = 0

                    price = round(price, 2)
        return price

    def product_delete(self, link):
        pr = ProductModel.objects.filter(link=link).first()
        if pr is not None:
            pr.is_deleted = True
            pr.save()

    def prepare_data(self, data, shop_instance):
        data_content = {}
        if 'name' in data:
            data['name'] = utils.remove_html_tags(data['name'])
            data['name'] = data['name'].replace('\n','').strip()
            data_content['name'] = data['name']
            data_content['slug'] = slugify(data['name'])
        if 'quantity' in data:
            if data['quantity'] is not None:
                data_content['stock'] = int(data['quantity'])
                if data_content['stock'] < 1:
                    data_content['is_deleted'] = False
        if 'category' in data:
            if data['category'] is None:
                data['category'] = 'diğer'
            cat, is_category = self.check_category(data['category'], shop_instance)

            if is_category.match is not None:
                data_content['category_id'] = is_category.match.id
                data_content['category'] = is_category.match
            else:
                data_content['category_id'] = is_category.id
                data_content['category'] = is_category


        if 'brand' in data:
            brnd, brand = self.check_brand(data['brand'])
            data_content['brand_id'] = brand.id
            data_content['brand'] = brand
        if 'link' in data:
            data_content['link'] = data['link'].strip().replace(' ','')
        if 'model_code' in data:
            data_content['model_code'] = data['model_code']
        if 'barcode' in data:
            data_content['barcode'] = data['barcode']
        if 'sku' in data:
            data_content['sku'] = data['sku']
        if 'stock' in data:
            data_content['quantity'] = data['quantity']
        if 'price' in data:
            data_content['price'] = self.price_fix(data['price'])
        if 'description' in data:
            data_content['description'] = data['description']
        if 'cargo_price' in data:
            data_content['cargo_price'] = self.price_fix(data['cargo_price'])
            if data_content['cargo_price'] is None or data_content['cargo_price'] == 'None':
                data_content['cargo_price'] = 0
        if 'kdv' in data:
            if data['kdv'] != '':
                data_content['kdv'] = data['kdv']
        if 'sub_merchant_shop' in data:
            if 'sub_merchant_id' in data:
                sub_merchant_id = data['sub_merchant_id']
            else:
                sub_merchant_id = None
            sub_merchant = self.check_submerchant(data['sub_merchant_shop'], shop_instance, sub_merchant_id)
            data_content['sub_merchant_shop'] = sub_merchant
        data_content['shop_id'] = shop_instance.id
        data_content['shop'] = shop_instance
        if 'image' in data:
            data['image'] = data['image'].strip().replace("\\n", "")
            if data['image'].startswith('/_next/image?url='):
                data['image'] = data["image"].replace('/_next/image?url=', '')
                data['image'] = unquote(data['image'])
                image = data['image'].split('.webp')
                if len(image) > 0:
                    data['image'] = f'{image[0]}.webp'

            if data['image'].startswith('//'):
                data['image'] = f'https:{data["image"]}'
            if data['image'].startswith('images'):
                data['image'] = f'{shop_instance.url}{data["image"]}'
            if data['image'].startswith('../../'):
                data["image"] = data["image"].replace('../../', shop_instance.url)
            if data['image'].startswith('./'):
                data['image'] = data["image"].replace('./', shop_instance.url)
            if data['image'].startswith('/'):
                data['image'] = f'{shop_instance.url}{data["image"]}'
            data_content['image'] = data['image']
        if 'is_deleted' not in data:
            data_content['is_deleted'] = False
        if 'avaible' in data:
            data_content['is_deleted'] = True
        if 'availability' in data:
            if data['availability'] == 'out of stock':
                data_content['is_deleted'] = True
            if data['availability'] == '0':
                data_content['is_deleted'] = True
        if 'spects' in data:
            if len(data['spects']) > 0:
                data_content['spects'] = data['spects']
        return data_content

    def check_brand(self, product_brand):
        if product_brand == '' or product_brand is None:
            product_brand = 'Diğer'
        product_brand = product_brand.lower()
        brand = BrandModel.objects.filter(name=product_brand).first()
        if brand is None:
            brand = BrandModel.objects.create(name=product_brand.lower())

        return {'id': brand.id, 'name': brand.name}, brand

    def check_submerchant(self, product_seller, shop_instance, product_merchant_id=None):
        product_seller = str(product_seller).lower()
        if product_seller=='':
            product_seller = shop_instance.name.lower()

        data = {
            'name': product_seller,
            'merchant': product_merchant_id,
            'shop': shop_instance.id,
        }

        is_sub_merhant = SubMerchantModel.objects.filter(name=product_seller).first()
        if is_sub_merhant is None:
            serializer = SubMerchantSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            sub_merchant = serializer.save()
        else:
            sub_merchant = is_sub_merhant

        return sub_merchant

    def save_productv2(self, data):
        spec_progress([data])
        image = None
        if 'image' in data:
            image = data['image']
            del data['image']
        product = ProductModel.objects.filter(link=data['link']).first()
        if product:
            serializer = ProductsSerializer(product, data=data, partial=True)
        else:
            serializer = ProductsSerializer(data=data)

        serializer.is_valid(raise_exception=True)
        product = serializer.save()
        if product:
            if image is not None:
                upload_images(image, product_id=product.id)

    def save_product(self, datas, seen_links):
        images = []
        spec_progress.delay(datas)
        for data in datas:
            images.append({'image': data['image'], 'link': data['link']})
            del data['image']
            if 'spects' in data:
                del data['spects']

        is_exist = ProductModel.objects.filter(link__in=seen_links).values_list('link', flat=True)
        existing_links = set(is_exist)
        create_datas = []
        update_datas = []
        for item in datas:
            if item['link'] not in existing_links:
                item['updated_at'] = timezone.now()
                create_datas.append(item)
            else:
                update_datas.append(item)
        links = [data['link'] for data in update_datas]
        prs = ProductModel.objects.filter(link__in=links)
        product_dict = {product.link: product for product in prs}
        product_models = []

        for data in update_datas:
            product = product_dict.get(data['link'])  # İlgili ProductModel nesnesini alıyoruz
            if product:
                data['updated_at'] = timezone.now()
                for key, value in data.items():
                    setattr(product, key, value)
                product_models.append(product)
        try:
            if update_datas:
                ProductModel.objects.bulk_update(product_models, list(update_datas[0].keys()))
        except Exception as e:
            print('bulk_update')
            print(e)
            SynchronizeModel.objects.create(shop_id=update_datas[0]['shop_id'], error=e, data=str(update_datas))
        try:
            if create_datas:
                bulk_datas = [
                    ProductModel(**data) for data in create_datas
                ]
                ProductModel.objects.bulk_create(bulk_datas)
        except Exception as e:
            print(e)
            print('bulk_create')
            SynchronizeModel.objects.create(shop_id=create_datas[0]['shop_id'], error=e, data=str(create_datas))

        elasticsearch_bulk(datas)
        category_set_brand(datas)
        for image in images:
            print(image['image'])
            print(image['link'])
            upload_images(image['image'], link=image['link'])

    def check_category(self, product_category_name, shop_instance):
        
        parts = [seperate.strip() for seperate in product_category_name.split(">")]
        if len(parts) > 1:
            product_category_name = parts[-1]

        is_category = CategoriesModel.objects.filter(name=product_category_name, shop=shop_instance, is_deleted=False).first()
        is_main_category = CategoriesModel.objects.filter(name=product_category_name, shop__isnull=True,
                                                          is_deleted=False).first()
        if is_category is None:
            is_category = CategoriesModel.objects.create(name=product_category_name,
                                                         shop=shop_instance,
                                                         is_deleted=False)
        if is_main_category:
            if is_category.match is None:
                is_category.match = is_main_category
                is_category.save()
            else:
                is_category = is_category.match

        return {'id': is_category.id, 'name': product_category_name}, is_category

    def download_urlv2(self, url, save=False):
        try:
            response = requests.get(url, stream=True)
            # İstek başarılıysa
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

                # İçeriği parça parça alıyoruz
                data_content = b""
                for data in response.iter_content(chunk_size=1024):
                    data_content += data
                    progress_bar.update(len(data))

                progress_bar.close()

                # content_stream ile veriyi işleyeceğiz

                content_stream = io.BytesIO(data_content)
                # Dosya boyutunu hesaplıyoruz
                file_size = len(data_content)

                if save:
                    save_path = 'dosya.xml'
                    with open(save_path, 'wb') as file:
                        file.write(data_content)
                    print(f"File saved to {save_path}")

                return data_content, content_stream, file_size
            else:
                print("Dosya indirilemedi. Hata kodu:", response.status_code)

        except requests.exceptions.RequestException as e:
            print("Bir hata oluştu:", e)



    def download_url(self, url, save=False):
        session = requests.Session()
        retry = Retry(
            total=10,  # Total number of retries
            backoff_factor=1,  # Time to wait between retries
            status_forcelist=[429, 500, 502, 503, 504],  # Retry on these HTTP status codes
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        try:
            response = session.get(url, headers=self.headers, verify=False, stream=True, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(e)
            SynchronizeModel.objects.create(error=e, data=url, script_file=sys.argv[0])
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
        return data_content, content_stream, file_size_bytes

    def check_url(self, url):
        is_syncronize = SynchronizeUrlsModel.objects.filter(url=url, is_deleted=False).exists()
        if ('ap/signin' in url or
                'ap/register' in url or
                'whatsapp' in url or
                'uye/giris' in url):
            return True
        return is_syncronize

    def is_productv2(self, soup, shop):
        map_all = shop.html_map.order_by('id').all()
        data = {}
        for item in map_all:
            aatr_filter = {}
            attrs = item.tag_attr.replace(', style="background-color: rgba(255, 215, 0, 0.5);"', '').split(',')
            for attr in attrs:
                att = attr.strip().split('=')
                if att[0] not in ['class', 'id', 'style', 'src', 'href', 'title',
                                  'data-source-link-object-id',
                                  'data-source-generation',
                                  'data-thumb',
                                  'data-ui-id',
                                  'data-type',
                                  'role',
                                  'aria-label',
                                  'data-zoom',
                                  'data-wix-price','content','component-id']:
                    if len(att)>1:
                        aatr_filter[att[0]] = att[1].replace('"', '')
            object = soup.find_all(item.tag, class_=item.tag_class, id=item.tag_id, attrs=aatr_filter)
            if len(object)>0:
                if item.type == 'brand':
                    if len(object) == item.order:
                        item.order =  item.order-1
                    if len(object) <= item.order:
                        item.order = len(object)-1

                    if 'fetchpriority' in str(object[item.order]):
                        try:
                            data[item.type] = object[item.order].find('img')['title']
                        except:
                            pass
                    elif 'value' in str(object[item.order]):
                        try:
                            data[item.type] = object[item.order]['value']
                        except:
                            data[item.type] = object[item.order].text

                    else:
                        pass

                elif item.type == 'image':
                    if len(object) > item.order:
                        image = object[item.order].find('img')
                        if image is not None:
                            try:
                                if 'data-img' in str(image):
                                    data[item.type] = image['data-img']
                                elif 'data-srcset' in str(image):
                                    data[item.type] = image['data-srcset']
                                elif 'data-src' in str(image):
                                    data[item.type] = image['data-src']
                                else:
                                    data[item.type] = image['src']
                            except:
                                print('*********image**********')
                                print(image)
                        else:
                            image = object[item.order].find('div')
                            print(image)
                            if 'data-img' in str(image):
                                image = image['data-img']
                            if image is not None:
                                data[item.type] = image
                else:
                    if len(object) < item.order:
                        object = object[len(object)-1]
                    else:
                        if len(object) <= item.order:
                            object = object[item.order-1]
                        else:
                            object =  object[item.order]
                    if item.type == 'price':
                        for muted in object.find_all("span", class_="text-muted"):
                            muted.decompose()


                    if object.text != '':
                        if item.type == 'price':
                            data[item.type] = object.text
                            #price = self.ai_price(object)
                            #if price is not None:
                            #    data[item.type] = price
                        else:
                            if item.type == 'category':
                                if len(object.findAll('li'))>1:
                                    if len(object.findAll('li')) > 2:
                                        data[item.type] = object.findAll('li')[-3].text
                                    else:
                                        data[item.type] = object.findAll('li')[-2].text
                                else:
                                    cats = object.text.split('\n')
                                    cats = [item for item in cats if item != '']
                                    if len(cats)>1:
                                        data[item.type] = cats[-2]
                                    else:
                                        data[item.type] = object.text
                                #fazla karakterleri temizle
                                if data[item.type] is not None:
                                    data[item.type] = data[item.type].replace('\n', '').strip()
                            else:
                                data[item.type] = object.text


                    if item.type == 'avaible':
                        style = object.get("style", "")
                        if "display: none;" in style:
                            del data[item.type]
                        text = object.getText().replace(' ', '')
                        if text=='SepeteEkle':
                            del data[item.type]
                        # if item.type == 'price':
                        #     for span in object.find_all('span'):
                        #         span.decompose()



                    # if item.type=='price':
                    #     print('*****')
                    #     print('burada')
                    #     print(data[item.type])
                    #     #print(object)
                    #     print('****bitti')
                        # results = nlp(str(object))
                        # prices = []
                        # for result in results:
                        #     if result['entity_group'] == 'PRICE':
                        #         print(result)
                        #         if result['score'] > 0.6:
                        #             prices.append(self.price_fix(result['word']))
                        # if len(prices)>0:
                        #     lowest_price = min(map(float, prices))
                        #     data[item.type] = lowest_price
        return data

    def ai_price(self, object):
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json"
        }
        dt = {
            "html_content": str(object)
        }
        response = requests.post(os.getenv('AI_URL') + 'find-prices/', headers=headers, data=json.dumps(dt))
        if response.status_code == 200:
            res = response.json()
            if res['indirimli_price'] is None:
                return res['price']
            else:
                return res['indirimli_price']

    def is_product(self, soup, shop, url):
        # ürün image
        product_image = self.parse_html.product_image(soup)

        # Ürün başlığı
        product_title = self.parse_html.product_title(soup)

        # sku
        sku = self.parse_html.product_sku(soup)

        # quantity
        quantity = self.parse_html.product_quantity(soup)

        # Ürün kategorisi
        category = self.parse_html.product_category(soup)

        # Ürün açıklaması
        product_desction = self.parse_html.product_description(soup)

        # Ürün fiyatı
        product_price = self.parse_html.product_price(soup)

        # Ürün marka
        product_brand = self.parse_html.product_brand(soup)

        # Ürün barcode ean
        ean = self.parse_html.product_ean(soup)

        # submerchant
        sub_merchant = self.parse_html.sub_merchant(soup)

        # availability
        availability = self.parse_html.availability(soup)

        # spects
        spects = self.parse_html.spects(soup)

        if availability == False:
            self.product_delete(url)
            return False, {'is_deleted': True}
        if sub_merchant is None:
            sub_merchant = shop.shop_title
        if product_image is not None:
            if not product_image.startswith('https:'):
                if product_image.startswith('//'):
                    product_image = f'https:{product_image}'
                else:
                    new_url = urlparse(url)
                    product_image = f'{new_url.scheme}://{new_url.netloc}{product_image}'
        data = {
            'name': product_title,
            'price': product_price,
            'image': product_image,
            'sub_merchant_shop': sub_merchant
        }
        if all(value is not None for value in data.values()):
            data['description'] = product_desction
            data['sku'] = sku
            data['quantity'] = quantity
            data['barcode'] = ean
            data['brand'] = product_brand
            data['category'] = category
            data['availability'] = availability
            data['spects'] = spects
            return True, data
        else:
            return False, data

    def get_updated_products(self, product, driver=None):
        if (product.shop.sync_service==5 or
                product.shop.sync_service==7 or
                product.shop.id==14 or
                product.shop.is_browser==True):
            try:
                driver.get(product.link)
                page_source = driver.page_source
            except Exception as e:
                print(e)
                SynchronizeModel.objects.create(error=e, data=product.id, shop=product.shop,script_file=sys.argv[0])
        else:
            try:
                scraper = cloudscraper.create_scraper()
                page_source = scraper.get(product.link).text
                #page_source = requests.get(product.link, headers=self.headers, timeout=30, allow_redirects=True)
                print(page_source.status_code)
                if page_source.status_code == 404:
                    product.is_deleted = True
                    product.save()
                    return True
                else:
                    page_source = page_source.text
            except Exception as e:
                product.is_deleted = True
                product.save()
                return True
        soup = BeautifulSoup(page_source, 'html.parser')
        data = self.is_productv2(soup, product.shop)
        data['link'] = product.link
        print(data)
        save_data = self.prepare_data(data, product.shop)
        if 'price' in data:
            price_history(product.price, save_data['price'], product.shop.id, None, product.id)
            if product.price != save_data['price']:
                product.price = save_data['price']
        else:
            save_data['is_deleted'] = True
        product.host_name = None
        product.is_deleted = save_data['is_deleted']
        product.save()
        if product.image is None:
            if 'image' in save_data:
                upload_images(save_data['image'], product_id=product.id)
        return True