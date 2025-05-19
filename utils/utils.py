import secrets
import string
import hashlib
import json
import uuid
import re
import os
from django.db import connection

from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

def generate_custom_random_key(length, use_punctuation=False):
    characters = string.ascii_letters + string.digits
    if use_punctuation:
        characters += string.punctuation
    return ''.join(secrets.choice(characters) for i in range(length))

def parent_match(parent_id):
    query = 'SELECT * FROM products_match WHERE to_productmodel_id=%s'
    params = [parent_id]
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row is not None:
            return row[1]
def generate_random_string(length=6):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(secrets.choice(characters) for _ in range(length))
    return random_string

def get_all_children(self, category):
    if category is not None:
        children = category.get_children()
        all_children = list(children)  # Start with the immediate children
    else:
        all_children = []

    # Recursively fetch children of each child category
    for child in all_children:
        all_children.extend(self.get_all_children(child))
    return all_children

def custom_hash(input_string):
    hasher = hashlib.new('sha256')
    hasher.update(input_string.encode())
    # Add more steps or manipulations here as needed
    return hasher.hexdigest()


def generate_cache_key(input_string):
    # Generate a hash of the input string
    hash_object = hashlib.md5(input_string.encode())
    return hash_object.hexdigest()


def filters(request, response):
    filters = request.GET.get('filters', None)
    orderBy = request.GET.get('orderBy', '')
    sortBy = request.GET.get('sortBy', 'id')

    if orderBy == 'desc':
        orderBy = '-'
    else:
        orderBy = ''

    if filters is not None:
        flter = {}
        try:
            filters_ = json.loads(filters)
        except:
            filters_ = {}
        for item in filters_:
            if filters_[item] != '' and filters_[item] is not None:
                flter[item] = filters_[item]
            response = response.filter(**flter)
    response = response.order_by(orderBy + sortBy).all()
    return response


def generate_unique_id():
    return str(uuid.uuid4())


def remove_html_tags(text):
    """Remove html tags from a string"""
    clean = re.compile('<.*?>')
    if text is not None:
        return re.sub(clean, '', text)
    else:
        return ''

def fix_character(string):
    string = string.replace('İ', 'i')
    return string

def get_all_children(category):
    if category is not None:
        children = category.get_children()
        all_children = list(children)  # Start with the immediate children
        children = list(children)  
    else:
        all_children = []
        children = [] 

    # Recursively fetch children of each child category
    for child in children:
        all_children.extend(get_all_children(child))
    return all_children

def calculate_file_hash(content_stream, hash_algo='sha256'):
    """Calculate the hash of a file."""

    # Choose the hashing algorithm
    hash_func = getattr(hashlib, hash_algo.lower(), None)
    if not hash_func:
        raise ValueError(f"Unsupported hash algorithm: {hash_algo}")

    # Calculate the hash of the file
    hash_object = hash_func()
    while True:
        data = content_stream.read(65536)  # Read in chunks to conserve memory
        if not data:
            break
        hash_object.update(data)

    return hash_object.hexdigest()

def driver_self(remote=False):
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
