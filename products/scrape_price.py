import requests
from bs4 import BeautifulSoup
import re

TAGS_TO_REMOVE = ['footer', 'script', 'a', 'style', 'title', 'input']

def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    for tag in TAGS_TO_REMOVE:
        for element in soup.find_all(tag):
            element.decompose()
    
    for class_name in ['navbar', 'similar-products']:
        for element in soup.find_all(class_=class_name):
            element.decompose()
    
    for element in soup.find_all(class_=lambda class_name: class_name and 'price2' in class_name):
        element.decompose()
    
    main_content = soup.find('main') or soup.find('div', {'id': 'main-content'}) or soup.find('div', {'class': 'main-content'})
    if main_content:
        soup = BeautifulSoup(str(main_content), 'html.parser')
    
    for element in soup.find_all():
        if not element.contents or not element.get_text(strip=True):
            element.decompose()
    
    for element in soup.find_all('s'):
        element.decompose()
    
    for element in soup.find_all(text=True):
        if not re.search(r'\d+', element) and not re.search(r'₺|TL', element):
            element.extract()
    
    return soup

def extract_price_from_html(html):
    price_classes = ['pd-price-new', 'product-price-new']
    for class_name in price_classes:
        price_element = html.find(class_=class_name)
        if price_element:
            price = re.search(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', price_element.text)
            if price:
                return price.group()

    price_element = html.find(id="productPriceView")
    if price_element:
        price = re.search(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', price_element.text)
        if price:
            return price.group()

    price_elements = html.find_all(class_=re.compile(r'.*price.*', re.IGNORECASE))
    if price_elements:
        for element in price_elements:
            price = re.search(r'\d{1,3}(?:\.\d{3})*(?:,\d+)?', element.text)
            if price:
                return price.group()
    
    price_pattern = r'₺\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d{1,3}(?:\.\d{3})*(?:,\d+)?\s*(?:TL|₺)'
    price_match = re.search(price_pattern, html.get_text())
    if price_match:
        return price_match.group()
    
    return "Price not found"

def extract_store_name(url):
    store_name = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return store_name.group(1) if store_name else "Unknown store"

def scrape_price(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            cleaned_html = clean_html(response.text)
            price = extract_price_from_html(cleaned_html)
            store_name = extract_store_name(url)
            return {'store': store_name, 'price': price}
        else:
            return {'error': 'Failed to fetch product page'}
    except Exception as e:
        return {'error': str(e)}

