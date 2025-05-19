import re
import json


class ParseHtml:
    def __init__(self):
        pass

    def product_image(self, soup):
        product_image_ = None

        #ptt avm
        if product_image_ is None:
            image_tag = soup.find('div', class_='comment-box-image-container')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['src']
        if product_image_ is None:
            image_tag = soup.find('div', class_='product-image')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['src'] if image_tag else None
        if product_image_ is None:
            image_tag = soup.find('div', class_='gallery-modal-content')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['src'] if image_tag else None
        if product_image_ is None:
            image_tag = soup.find('a', class_='thumbnail')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['src'] if image_tag else None
        if product_image_ is None:
            image_tag = soup.find('image-zoom')
            if image_tag is not None:
                if 'regular' in image_tag.attrs:
                    product_image_ = image_tag['regular']
        if product_image_ is None:
            image_tag = soup.find('div', class_='andro_product-single-thumb')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['src'] if image_tag else None
        if product_image_ is None:
            image_tag = soup.find('div', class_='swogo-image-wraper')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['src'] if image_tag else None
        if product_image_ is None:
            image_tag = soup.find('figure', class_='responsive responsive-changed img-loaded')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                product_image_ = image_tag['data-srcset'] if image_tag else None

        if product_image_ is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                try:
                    response = json.loads(script_tag.text)
                    pr_data = response['productState']['product']
                    if pr_data is not None:
                        if len(pr_data['variants']) > 0:
                            product_image_ = pr_data['variants'][0]['thumbnail']
                except:
                    pass
        if product_image_ is None:
            image_tag = soup.find('img', class_='hb-HbImage-view__image')
            if image_tag is not None:
                product_image_ = image_tag['src']
        if product_image_ is None:
            image_tag = soup.find('img', {'alt': 'product image'})
            if image_tag is not None:
                product_image_ = image_tag['src']

        if product_image_ is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                try:
                    json_data = json.loads(script_tag.string)
                    if 'productStructuredJson' in json_data['props']['pageProps']:
                        product_image_ = \
                            json_data['props']['pageProps']['productStructuredJson']['mainEntity']['offers']['itemOffered'][
                                0][
                                'image'][0]['contentUrl']
                except:
                    pass
        # dermoevim
        if product_image_ is None:
            image_tag = soup.find('meta', {'name': 'og:image'})
            if image_tag is not None:
                product_image_ = image_tag['content']
        if product_image_ is None:
            image_tag = soup.find('img', class_='videoImagePreview')
            if image_tag is not None:
                product_image_ = image_tag['src']

        if product_image_ is None:
            image_tag = soup.find('div', id='prd-images')
            if image_tag is not None:
                image_tag = image_tag.find('img', class_='img-fluid')
                if image_tag is not None:
                    product_image_ = image_tag['src']

        if product_image_ is None:
            image_tag = soup.find('script', type='application/ld+json')
            if image_tag is not None:
                try:
                    json_data = json.loads(image_tag.string)
                    if 'image' in json_data:
                        product_image_ = json_data.get('image', [])[0]
                except:
                    pass
        if product_image_ is None:
            image_tag = soup.find('img', class_='object-contain w-full h-full cursor-pointer')
            if image_tag is not None:
                product_image_ = image_tag['src']

        # irhaltarim
        if product_image_ is None:
            image_tag = soup.find('div', class_='u_foto_buyuk')
            if image_tag is not None:
                image_tag = image_tag.find('a', {'data-item': 'u_foto_galeri_1'})
                if image_tag is not None:
                    product_image_ = image_tag['href']

        #enucuztesisat
        if product_image_ is None:
            image_tag = soup.find('img', id='imgUrunResim')
            if image_tag is not None:
                product_image_ = image_tag['src']

        # asil kirtasiye
        if product_image_ is None:
            image_tag = soup.find('div', class_='image-wrapper')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['src']

        # via sports
        if product_image_ is None:
            image_tag = soup.find('div', id='thumb0')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['src']
        # idefix
        if product_image_ is None:
            image_tag = soup.find('img', class_='z-10 z-10')
            if image_tag is not None:
                product_image_ = image_tag['src']
        # aloanne
        if product_image_ is None:
            image_tag = soup.find('a', class_='thumbnail')
            if image_tag is not None:
                image_tag = image_tag.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['src']
        # adanamedikal
        if product_image_ is None:
            image_tag = soup.find('img', class_='wp-post-image')
            if image_tag is not None:
                product_image_ = image_tag['src']
        # dekamedikal
        if product_image_ is None:
            image_tag = soup.find('div', {'u_foto_buyuk'})
            if image_tag is not None:
                image_tag = soup.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['src']
        # bollucuoglu
        if product_image_ is None:
            image_tag = soup.find('figure', class_='pro_gallery_item')
            if image_tag is not None:
                product_image_ = image_tag.find('img')
                if image_tag is not None:
                    product_image_ = image_tag['data-srcset']

        # gleamaccessories
        if product_image_ is None:
            image_tag = soup.find('img', class_='product__image')
            if image_tag is not None:
                product_image_ = image_tag['data-src']

        # teknosa
        if product_image_ is None:
            script_tag = soup.find('script', text=re.compile(r'product_image_url'))
            if script_tag:
                match = re.search(r'"product_image_url":"(https?://[^"]+)"', script_tag.string)
                if match:
                    product_image_ = match.group(1)
        # bogadan
        if product_image_ is None:
            json_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_scripts:
                try:
                    json_data = json.loads(script.string)  # Load JSON data
                    pretty_json = json.dumps(json_data, indent=4, ensure_ascii=False)  # Beautify JSON

                    if 'offers' in pretty_json:
                        # json_data = json_data.get("offers")
                        if 'image' in json_data:
                            if len(json_data['image']) > 0:
                                product_image_ = json_data['image'][0]
                except:
                    pass
        return product_image_

    def product_title(self, soup):
        product_title = None

        if product_title is None:
            title_tag = soup.find('div', class_='product-title')  # Başlık için uygun class'ı bulun
            if title_tag is not None:
                title_tag = soup.find('h1', class_='product-title')
            product_title = title_tag.text.strip() if title_tag else None

        if product_title is None:
            title_tag = soup.find('h1', class_='pr-new-br')  # Başlık için uygun class'ı bulun
            if title_tag is not None:
                product_title = title_tag.text.strip() if title_tag else None

        if product_title is None:
            title_tag = soup.find('div', class_='entry-content content-title d-none d-xl-block')
            if title_tag is not None:
                product_title = title_tag.text.strip() if title_tag else None

        if product_title is None:
            title_tag = soup.find('div', class_='andro_product-single-content')
            if title_tag is not None:
                title_tag = title_tag.find('h3')
                if title_tag is not None:
                    product_title = title_tag.text.strip() if title_tag else None

        if product_title is None:
            title_tag = soup.find('div', class_='psm-title')
            if title_tag is not None:
                product_title = title_tag.text.strip() if title_tag else None

        if product_title is None:
            title_tag = soup.find('h1', class_='product-name')
            if title_tag is not None:
                product_title = title_tag.text.strip() if title_tag else None

        if product_title is not None:
            product_title = product_title.replace('\n', '')

        if product_title is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    if len(pr_data['variants']) > 0:
                        product_title = pr_data['variants'][0]['name']

        if product_title is None:
            product_title_tag = soup.find('h1', {'data-test-id': 'title'})
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        if product_title is None:
            product_title_tag = soup.find('h1', class_='text-[1.375rem] leading-[1.875rem] mb-[0.375rem] font-medium')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        if product_title is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    product_title = json_data['props']['pageProps']['productStructuredJson']['mainEntity']['offers'][
                        'name']

        if product_title is None:
            product_title_tag = soup.find('div', class_='ProductName')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        if product_title is None:
            product_title_tag = soup.find('h1', class_='product-title')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        if product_title is None:
            product_title_tag = soup.find('div', class_='p-float-sag')
            if product_title_tag is not None:
                product_title_tag = product_title_tag.find('table')
                if product_title_tag is not None:
                    product_title_tag = product_title_tag.find_all('tr')
                    product_title = product_title_tag[0].text.strip() if product_title_tag else None

        if product_title is None:
            product_title_tag = soup.find('div', class_='product-detail')
            if product_title_tag is not None:
                product_title_tag = product_title_tag.find('h1', class_='text-huge')
                if product_title_tag is not None:
                    product_title = product_title_tag.text.strip() if product_title_tag else None

        #ptt avm
        if product_title is None:
            product_title_tag = soup.find('h1', class_='text-lg font-medium break-word')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # sporcu pazarı
        if product_title is None:
            product_title_tag = soup.find('h1', class_='product_heading')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # asilkirtasiye
        if product_title is None:
            product_title_tag = soup.find('h1', id='product-title')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # idefix
        if product_title is None:
            product_title_tag = soup.find('div', class_='flex justify-between w-full')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # adanamedikal
        if product_title is None:
            product_title_tag = soup.find('h1', class_='product_title entry-title')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # 4mmedikal
        if product_title is None:
            product_title_tag = soup.find('div', class_='title page-title')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # dermoevim
        if product_title is None:
            product_title_tag = soup.find('h2', id='baslik')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # dekamedikal
        if product_title is None:
            product_title_tag = soup.find('div', class_='baslik')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # cimnastikcim
        if product_title is None:
            product_title_tag = soup.find('h1', id='productName')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # childgen
        if product_title is None:
            product_title_tag = soup.find('h1', class_='w-full')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # bulentsavas
        if product_title is None:
            product_title_tag = soup.find('div', class_='product-title')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # bollucuoglu
        if product_title is None:
            product_title_tag = soup.find('h1', class_='product_name')
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # elmavm
        if product_title is None:
            product_title_tag = soup.find('h2', {'itemprop': 'name'})
            if product_title_tag is not None:
                product_title = product_title_tag.text.strip() if product_title_tag else None

        # teknosa
        if product_title is None:
            title = soup.find('input', id="productNameSeller")
            if title:
                product_title = title['value']

        # gleamaccessories
        if product_title is None:
            title = soup.find('h1', class_="product-info__title")
            if title:
                product_title = title.text.strip()

        if product_title is not None:
            product_title = product_title.replace('\r', '').replace('\n', '').replace('  ', '').strip()
        return product_title

    def product_sku(self, soup):
        sku = soup.find('td', string='Stok Kodu')
        if sku is not None:
            sku = sku.find_next('td').text
        if sku is not None:
            sku = soup.find('div', string='Stok Kodu')
            if sku is not None:
                sku = sku.find_next('div').text

        if sku is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    if len(pr_data['variants']) > 0:
                        sku = pr_data['variants'][0]['sku']

        if sku is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    sku = \
                        json_data['props']['pageProps']['productStructuredJson']['mainEntity']['offers']['itemOffered'][
                            0][
                            'sku']

        return sku

    def product_quantity(self, soup):
        quantity = soup.find('td', string='Stok Adeti')
        if quantity is not None:
            quantity = quantity.find_next('td').text.replace(':', '').strip()
        return quantity

    def product_category(self, soup):
        category = None

        if category is None:
            category_tag = soup.find('button', class_='js-add-to-cart')  # Kategori için uygun yapıyı bulun
            if category_tag is not None:
                if 'data-product-subcategory' in category_tag:
                    category = category_tag['data-product-subcategory']

        if category is None:
            category_tag = soup.find_all('li', class_='breadcrumb-item')
            if len(category_tag) > 0:
                category = category_tag[-1].text
            if len(category_tag) > 2:
                category = category_tag[-2].text
            else:
                category = None

        if category is None:
            category_tag = soup.find_all('a', class_='product-detail-breadcrumb-item')
            if len(category_tag) > 0:
                category = category_tag[-1].text
            if len(category_tag) > 2:
                category = category_tag[-2].text

        if category is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    category = pr_data['categories'][len(pr_data['categories']) - 1]['categoryName']

        if category is None:
            category_tag = soup.find_all('div', class_='whitespace-nowrap max-w-[50rem] truncate')
            if len(category_tag) > 0:
                category = category_tag[-1].find('a').text
            if len(category_tag) > 2:
                category = category_tag[-2].find('a').text
            else:
                category = None

        if category is None:
            category_tag = soup.find('ul', class_='breadcrumb')
            if category_tag is not None:
                category_tag = category_tag.find_all('li', {'itemprop': 'itemListElement'})
                if len(category_tag) > 0:
                    category = category_tag[-1].find('a').text
                if len(category_tag) > 2:
                    category = category_tag[-2].find('a').text

        if category is None:
            category_tag = soup.find('ul', class_='breadcrumbs')
            if category_tag is not None:
                category_tag = category_tag.find_all('li', {'itemprop': 'itemListElement'})
                if len(category_tag) > 0:
                    category = category_tag[-1].find('a').text
                if len(category_tag) > 2:
                    category = category_tag[-2].find('a').text

        if category is None:
            category_tag = soup.find('a', {'title': 'Anasayfa'})
            if category_tag is not None:
                category_tag = category_tag.find_parent('ul')
                if category_tag is not None:
                    category_tag = category_tag.find_all('li')
                    if len(category_tag) > 0:
                        category = category_tag[-1].text
                    if len(category_tag) > 2:
                        category = category_tag[-2].text

        if category is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    category = \
                        json_data['props']['pageProps']['productStructuredJson']['mainEntity']['offers']['itemOffered'][
                            0][
                            'category']

        if category is None:
            category_tag = soup.find('div', class_='category-tree overflow-hidden mx-4 lg:mx-0')
            if category_tag is not None:
                category_tag = category_tag.find_all('a')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        #asil kırtasiye
        if category is None:
            category_tag = soup.find('nav', class_='breadcrumb')
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        # dermoevim
        if category is None:
            category_tag = soup.find('div', class_='breadcrumb')
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text
        # dekamedikal
        if category is None:
            category_tag = soup.find('div', class_='kategori_link')
            if category_tag is not None:
                category_tag = category_tag.find_all('a')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        # cimnastikcim
        if category is None:
            category_tag = soup.find('div', ul='navigasyon')
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        # bollucuoglu
        if category is None:
            category_tag = soup.find('nav', class_='breadcrumb_nav')
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-3].text

        # aytticaret
        if category is None:
            category_tag = soup.find('ol', {'typeof': 'BreadcrumbList'})
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        # elmavm
        if category is None:
            category_tag = soup.find('ul', class_='breadcrumb')
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        # avrupasoft
        if category is None:
            category_tag = soup.find('ol', {'itemprop': 'breadcrumb'})
            if category_tag is not None:
                category_tag = category_tag.find_all('li')
                if len(category_tag) > 0:
                    category = category_tag[-1].text
                if len(category_tag) > 2:
                    category = category_tag[-2].text

        if category is None:
            category_tag = soup.find('div', class_='product-categories')  # Kategori için uygun yapıyı bulun
            if category_tag is not None:
                category_links = category_tag.find_all('a')
                if category_links:
                    category = category_links[-1].text.strip()
            else:
                category = soup.find('td', string='Kategoriler')
                if category is not None:
                    category = category.find_next('a').text

        if category is None:
            category = soup.find('div', string='Kategori')
            if category is not None:
                category = category.find_next('div').text

        if category is not None:
            category = category.replace('\n', '').strip()
        return category

    def product_description(self, soup):
        product_desction_ = None

        if product_desction_ is None:
            features_tag = soup.find('div', class_='product-desc-content')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', class_='product-desc-content')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', id='tab-urun-aciklamasi')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', class_='productDescriptionContent')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', class_='features-tab-content px-5 py-10 lg:p-20')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    product_desction_ = json_data['props']['pageProps']['productDetail']['item']['attributes'][
                        'description']

        if product_desction_ is None:
            features_tag = soup.find('div', class_='OnYaziContent')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', id='aciklama')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        #asil kırtasıye
        if product_desction_ is None:
            features_tag = soup.find('div', id='product-fullbody')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        #adanamedikal
        if product_desction_ is None:
            features_tag = soup.find('div', class_='electro-description')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # dermoevim
        if product_desction_ is None:
            features_tag = soup.find('div', class_='bilgilendirme')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # dekopratik
        if product_desction_ is None:
            features_tag = soup.find('div', class_='block-content')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # cimnastikcim
        if product_desction_ is None:
            features_tag = soup.find('div', id='productDetailTab')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # bulentsavas
        if product_desction_ is None:
            features_tag = soup.find('div', class_='product-detail')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # elmavm
        if product_desction_ is None:
            features_tag = soup.find('div', id='tab-description')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        if product_desction_ is None:
            features_tag = soup.find('div', class_='description')
            if features_tag is not None:
                product_desction_ = features_tag.text.strip()

        # features_tag = soup.find('div', class_='product-detail')  # Özellikler için uygun class'ı bulun
        # if features_tag is not None:
        #     product_desction_ = features_tag.text.strip() if features_tag else None
        return product_desction_

    def product_price(self, soup):
        product_price_ = None
        # enucuztesisat
        if product_price_ is None:
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string is not None:
                    match = re.search(r'var\s+productDetailModel\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        json_data = json.loads(match.group(1))
                        product_price_ = json_data['productPriceKDVIncluded']
                        break

        if product_price_ is None:
            price = soup.find('span', class_='discounted-selling-price')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('h3', class_='price-new')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('span', class_='prc-dsc')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('button', class_='js-add-to-cart')  # Kategori için uygun yapıyı bulun
            if price is not None:
                if 'data-price-with-discount' in price.attrs:
                    product_price_ = price['data-price-with-discount']
        #asanlaranahtar
        if product_price_ is None:
            price = soup.find('div', class_='product-price')
            if price is not None:
                price_new = price.find('div', class_='product-price-new')
                if price_new is not None:
                    product_price_ = price_new.text.strip()
                else:
                    price_new = price.find('div', class_='product-price-old')
                    if price_new is None:
                        price_new = price.find('span', class_='price-sales')
                        if price_new is None:
                            price = price.text.strip()
                            product_price_ = price
                        else:
                            product_price_ = price_new.text.strip()
                    else:
                        price = price_new.text.strip()
                        product_price_ = price
        if product_price_ is None:
            price = soup.find('span', class_='product-price price')
            if price is not None:
                product_price_ = price.text.strip()
        if product_price_ is None:
            price = soup.find('div', class_='product-price')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('div', class_='andro_product-price')
            if price is not None:
                product_price_ = price.find('span').text.strip()

        if product_price_ is None:
            price = soup.find('div', class_='swogo-price-without-discount')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    if len(pr_data['variants']) > 0:
                        product_price_ = pr_data['variants'][0]['price']
        if product_price_ is None:
            price = soup.find('div', {'data-test-id': 'price-current-price'})
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('span', class_='text-[1.125rem] xl:text-[1.375rem] leading-[1.875rem] font-medium')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    product_price_ = json_data['props']['pageProps']['productDetail']['item']['price']['discountedText']

        if product_price_ is None:
            price = soup.find('span', class_='spanFiyat')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('label', id='fiyatuser')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('span', id='shopPHPUrunFiyatYTL')
            if price is not None:
                product_price_ = price.text.strip()

        if product_price_ is None:
            price = soup.find('p', class_='text-lg text-blue-500 font-bold leading-tight')
            if price is not None:
                product_price_ = price.text.strip()

        #ptt avm
        if product_price_ is None:
            price = soup.find('div', class_='text-eGreen-700 font-semibold text-3xl')
            if price is not None:
                product_price_ = price.text.strip()

        # pazarama avm
        if product_price_ is None:
            price = soup.find('p', class_='text-4xl font-bold mb-2 text-gray-600')
            if price is not None:
                product_price_ = price.text.strip()

        # pazarama avm
        if product_price_ is None:
            price = soup.find('p', class_='text-4xl font-bold mb-2 text-red-600')
            if price is not None:
                product_price_ = price.text.strip()

        # sporcu pazarı
        if product_price_ is None:
            price = soup.find('div', class_='para')
            if price is not None:
                price = price.find('h1')
                if price is not None:
                    product_price_ = price.text.strip()

        # asil kirtasiye
        if product_price_ is None:
            price = soup.find('span', class_='product-price')
            if price is not None:
                product_price_ = price.text.strip()

        # adanamedikal
        if product_price_ is None:
            price = soup.find('p', class_='price')
            if price is not None:
                price = price.find('span', class_='woocommerce-Price-amount')
                if price is not None:
                    product_price_ = price.text.strip()

        # dermoevim
        if product_price_ is None:
            price = soup.find('div', class_='price')
            if price is not None:
                price = price.find('span', id='indirimli')
                if price is not None:
                    product_price_ = price.text.strip()

        # dekopratik
        if product_price_ is None:
            price = soup.find('div', class_='product-price-new')
            if price is not None:
                product_price_ = price.text.strip()

        # dekamedikal
        if product_price_ is None:
            price = soup.find('div', class_='indirimli_fiyat')
            if price is not None:
                product_price_ = price.text.strip()

        # asil kirtasiye
        if product_price_ is None:
            price = soup.find('span', class_='product-price')
            if price is not None:
                product_price_ = price.text.strip()

        # gleamaccessories
        if product_price_ is None:
            price = soup.find("div", class_="product-info__price")
            if price is not None:
                product_price_ = price.text.strip()

        return product_price_

    def product_brand(self, soup):

        product_brand_ = None

        if product_brand_ is None:
            brand_tag = soup.find('button', class_='js-add-to-cart')
            if brand_tag is not None:
                if 'data-product-brand' in brand_tag:
                    product_brand_ = brand_tag['data-product-brand']

        if product_brand_ is None:
            brand_tag = soup.find('a', class_='product-brand')
            if brand_tag is not None:
                product_brand_ = brand_tag.text.strip()

        if product_brand_ is None:
            brand_tag = soup.find('div', class_='product-brand')  # Fiyat için uygun class'ı bulun
            product_brand_ = brand_tag.text.strip() if brand_tag else None
            if product_brand_ is None:
                product_brand_ = soup.find('td', string='Marka')
                if product_brand_ is not None:
                    product_brand_ = product_brand_.find_next('a').text.strip()

        if product_brand_ is None:
            product_brand_ = soup.find('div', string='Marka')
            if product_brand_ is not None:
                product_brand_ = product_brand_.find_next('div').text.strip()

        if product_brand_ is None:
            product_brand_ = soup.find('span', string='Marka:')
            if product_brand_ is not None:
                product_brand_ = product_brand_.find_next('a').text.strip()

        if product_brand_ is None:
            product_brand_ = soup.find('span', string='swogo-product-brand')
            if product_brand_ is not None:
                product_brand_ = product_brand_.text.strip()

        if product_brand_ is None:
            product_brand_tag = soup.find('a', class_='product-brand-name-with-link')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip()

        if product_brand_ is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    product_brand_ = pr_data['brand']

        if product_brand_ is None:
            product_title_tag = soup.find('a', {'data-test-id': 'brand'})
            if product_title_tag is not None:
                product_brand_ = product_title_tag.text.strip() if product_title_tag else None

        if product_brand_ is None:
            product_title_tag = soup.find('span',
                                          class_='text-[1.375rem] leading-[1.875rem] font-semibold cursor-pointer')
            if product_title_tag is not None:
                product_brand_ = product_title_tag.text.strip() if product_title_tag else None

        if product_brand_ is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    product_brand_ = \
                        json_data['props']['pageProps']['productStructuredJson']['mainEntity']['offers']['itemOffered'][
                            0][
                            'brand']['name']

        if product_brand_ is None:
            product_brand_tag = soup.find('div', class_='productMarka')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        if product_brand_ is None:
            product_brand_tag = soup.find('div', class_='product-code')
            if product_brand_tag is not None:
                product_brand_tag = product_brand_tag.find('a')
                if product_brand_tag is not None:
                    product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        if product_brand_ is None:
            product_brand_tag = soup.find('td', string='Marka:')
            if product_brand_tag is not None:
                product_brand_tag_a = product_brand_tag.find('a')
                if product_brand_tag_a is not None:
                    product_brand_ = product_brand_tag_a.text.strip() if product_brand_tag_a else None
                else:
                    product_brand_tag = product_brand_tag.find_next('td')
                    if product_brand_tag is not None:
                        product_brand_ = product_brand_tag.text.strip()
        if product_brand_ is None:
            product_brand_tags = soup.find_all('p', class_='product-code')
            if product_brand_tags is not None:
                for product_brand_tag in product_brand_tags:
                    product_brand_tag = product_brand_tag.find(string='Marka: ')
                    if product_brand_tag is not None:
                        product_brand_tag = product_brand_tag.find_next('strong')
                        if product_brand_tag is not None:
                            product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        if product_brand_ is None:
            product_brand_tag = soup.find('a', class_='text-blue-500 text-base font-semibold')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        #asilkırtasiye
        if product_brand_ is None:
            product_brand_tag = soup.find('a', id='brand-title')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        # 4mmedikal
        if product_brand_ is None:
            product_brand_tag = soup.find('div', class_='product-manufacturer')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        # dermoevim
        if product_brand_ is None:
            product_brand_tag = soup.find('a', class_='brand')
            if product_brand_tag is not None:
                product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        # avansas
        if product_brand_ is None:
            product_brand_tag = soup.find('div', class_='brandName')
            if product_brand_tag is not None:
                product_brand_tag = product_brand_tag.find('a')
                if product_brand_tag is not None:
                    product_brand_ = product_brand_tag.text.strip() if product_brand_tag else None

        return product_brand_

    def availability(self, soup):
        availability_ = None

        if availability_ is None:
            availability_tag = soup.find('button', string='Tükendi!')
            if availability_tag is not None:
                availability_ = False
        #ticimax
        if availability_ is None:
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                try:
                    json_data = json.loads(script_tag.string)
                    if 'offers' in json_data:
                        if json_data['offers']['availability'] == 'OutOfStock':
                            availability_ = False
                except:
                    pass
        if availability_ is None:
            availability_tag = soup.find('button', {'data-variant': 'secondary'})
            if availability_tag is not None:
                availability_tag = availability_tag.text.strip()
                if availability_tag == 'Gelince Haber Ver':
                    availability_ = False
        #enucuztesisat
        if availability_ is None:
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string is not None:
                    match = re.search(r'var\s+productDetailModel\s*=\s*({.*?});', script.string, re.DOTALL)
                    if match:
                        json_data = json.loads(match.group(1))
                        if 'products' in json_data:
                            if json_data['products'] is not None:
                                for pr in json_data['products']:
                                    stock = str(pr['stokAdedi'])
                                    if stock != '0.0':
                                        availability_ = None
                                        break
                            else:
                                if json_data['product'] is not None:
                                    stock = str(json_data['product']['stokAdedi'])
                                    if stock != '0.0':
                                        availability_ = None
                                        break
                                else:
                                    availability_ = False

        #sporcu pazarı
        if availability_ is None:
            availability_tag = soup.find('span', string='Stok Durumu:')
            if availability_tag is not None:
                availability_tag = availability_tag.find_next('strong')
                if availability_tag is not None:
                    availability_tag = availability_tag.text.strip()
                    if availability_tag == 'Stokta yok':
                        availability_ = False

        # 4mmedikal
        if availability_ is None:
            availability_tag = soup.find('li', class_='product-stock in-stock')
            if availability_tag is not None:
                availability_tag = availability_tag.find('span')
                if availability_tag is not None:
                    availability_tag = availability_tag.text.strip()
                    if availability_tag == 'Stokta yok':
                        availability_ = False
        return availability_

    def product_ean(self, soup):
        ean = None
        if ean is None:
            ean_tag = soup.find('button', class_='js-add-to-cart')
            if ean_tag is not None:
                if 'data-product-ean' in ean_tag.attrs:
                    ean = ean_tag['data-product-ean']

        if ean is None:
            ean = soup.find('div', string='EAN')
            if ean is not None:
                ean = ean.find_next('div').text
            if ean is not None:
                ean = soup.find('div', string='Ürün Kodu:')
                if ean is not None:
                    ean = ean.find('strong')
                    if ean is not None:
                        ean = ean.text.strip()

        if ean is None:
            ean = soup.find('label', class_='d-block mb-1')
            if ean is not None:
                ean = ean.find('strong')
                if ean is not None:
                    ean = ean.text.strip()

        if ean is None:
            script_tag = soup.find('script', text=re.compile(r'__PRODUCT_DETAIL_APP_INITIAL_STATE__'))

            # <script> tag'inden JSON kısmını çekelim
            if script_tag:
                # Script içerisindeki JSON verisini ayıklamak için regex kullanalım
                json_text = re.search(r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*(\{.*\});',
                                      script_tag.string)

                if json_text:
                    # JSON verisini ayrıştıralım
                    json_data = json.loads(json_text.group(1))

                    # barcode değerini çekelim
                    if len(json_data['product']['variants']) > 0:
                        ean = json_data['product']['variants'][0]['barcode']

        if ean is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    ean = pr_data['barcode']

        if ean is None:
            script_tag = soup.find('script', {'id': '__NEXT_DATA__'})
            if script_tag:
                json_data = json.loads(script_tag.string)
                if 'productStructuredJson' in json_data['props']['pageProps']:
                    ean = json_data['props']['pageProps']['productDetail']['item']['attributes']['barcode']

        # ticimax
        if ean is None:
            ean_code = soup.find_all('script')
            for ean_it in ean_code:
                ean_it = ean_it.text
                if 'EAN Kodu' in ean_it:
                    ean_pattern = r'\b\d{13}\b|\b\d{12}\b'
                    match = re.search(ean_pattern, ean_it)
                    ean = match.group(0)

        # dermoevim
        if ean is None:
            ean_code = soup.find('label', string='Barkod:')
            if ean_code is not None:
                ean_code = ean_code.find_parent('li')
                if ean_code is not None:
                    ean_pattern = r'\b\d{13}\b|\b\d{12}\b'
                    ean_code = ean_code.text.strip()
                    match = re.search(ean_pattern, ean_code)
                    ean = match.group(0)

        # denizlioptik
        if ean is None:
            ean_code = soup.find('span', class_='productcode')
            if ean_code is not None:
                ean_code = ean_code.text.strip()
                ean = ean_code.replace('(', '').replace(')', '')

        # bilisimport
        if ean is None:
            ean_code = soup.find('td', string='EAN Kodu')
            if ean_code is not None:
                ean_code = ean_code.find_next('td')
                if ean_code is not None:
                    ean_code = ean_code.text.strip()
                    ean = ean_code.replace('(', '').replace(')', '')

        if ean is None:
            ean_pattern = r'\b\d{13}\b|\b\d{12}\b'
            ean_code = soup.text.strip()
            match = re.search(ean_pattern, ean_code)
            if match is not None:
                ean = match.group(0)

        return ean

    def sub_merchant(self, soup):

        sub_merchant_ = None
        if sub_merchant_ is None:
            sub_merchant_tag = soup.find('button', class_='js-add-to-cart')
            if sub_merchant_tag is not None:
                if 'data-shop-name' in sub_merchant_tag.attrs:
                    sub_merchant_ = sub_merchant_tag['data-shop-name']

        if sub_merchant_ is None:
            sub_merchant_tag = soup.find('div', class_='swogo-product-seller-name')
            if sub_merchant_tag is not None:
                sub_merchant_ = sub_merchant_tag.text.strip()

        if sub_merchant_ is None:
            sub_merchant_tag = soup.find('div', class_='supplier-info')
            if sub_merchant_tag is not None:
                sub_merchant_tag = sub_merchant_tag.find('b')
                sub_merchant_ = sub_merchant_tag.text.strip()

        if sub_merchant_ is None:
            script_tag = soup.find('script', id='reduxStore')
            if script_tag is not None:
                response = json.loads(script_tag.text)
                pr_data = response['productState']['product']
                if pr_data is not None:
                    sub_merchant_ = pr_data['merchantName']

        if sub_merchant_ is None:
            sub_merchant_tag = soup.find('div', {'data-test-id': 'buyBox-seller'})
            if sub_merchant_tag is not None:
                sub_merchant_tag = sub_merchant_tag.find('a')
                sub_merchant_ = sub_merchant_tag.text.strip()

        if sub_merchant_ is None:
            script_tag = soup.find('span', string='Satıcı:')
            if script_tag is not None:
                script_tag = script_tag.find_next('a')
                if script_tag is not None:
                    sub_merchant_ = re.sub(r'\(.*?\)', '', script_tag.text).strip()

        if sub_merchant_ is None:
            sub_merchant_tag = soup.find('p', class_='flex text-gray-500 text-xxs !text-base')
            if sub_merchant_tag is not None:
                sub_merchant_tag = sub_merchant_tag.find('span', class_='text-blue-500')
                if sub_merchant_tag is not None:
                    sub_merchant_ = sub_merchant_tag.text.strip()

        #ptt avm
        if sub_merchant_ is None:
            sub_merchant_tags = soup.find_all('span')
            matching_spans = [span for span in sub_merchant_tags if span.get_text(strip=True) == 'Mağaza:']
            if matching_spans:
                sub_merchant_tag = matching_spans[0].find_next('a')
                if sub_merchant_tag is not None:
                    sub_merchant_ = sub_merchant_tag.text.strip()

        return sub_merchant_

    def spects(self, soup):
        features_list = []

        #trendyol
        if len(features_list) < 1:
            features_sections = soup.find_all('ul', class_='detail-attr-container')
            if features_sections is not None:
                for features in features_sections:
                    features_attr = features.find_all('li')
                    for feature in features_attr:
                        ftr = feature.find_all('span')
                        features_title = ftr[0].text
                        feature_values = ftr[1].text
                        if features_title != '':
                            if len(feature_values) < 200:
                                features_list.append({'title': features_title, 'value': [feature_values]})

        # pttavm
        if len(features_list) < 1:
            features_sections = soup.find_all('div', class_='select-none px-1 mb-2 w-full')
            if features_sections is not None:
                for features in features_sections:
                    if features is not None:
                        print(features)
                        try:
                            features_title = features.find('h3').text
                        except:
                            features_title = features.find('span').text

                        feature_values = features.find_all('button')
                        values_list = []
                        for value in feature_values:
                            values_list.append(value.text.strip())
                        features_list.append({'title': features_title, 'value': values_list})

        #teknosa
        if len(features_list) < 1:
            features_sections = soup.find('div', id='pdp-technical')
            if features_sections is not None:
                features_sections_ = features_sections.find_all('table', class_='table')
                for table in features_sections_:
                    features_sections_ = table.find_all('th')
                    features_sections_values = table.find_all('td', class_='')

                    for index, features in enumerate(features_sections_):
                        features_title = features.text.strip()
                        feature_values = features_sections_values[index].text.strip()
                        features_list.append({'title': features_title, 'value': [feature_values]})
        return features_list