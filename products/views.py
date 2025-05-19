# Create your views here.
import os
import random
import math
import base64
import requests
import cloudscraper

from user_agents import parse

from django.shortcuts import redirect, get_object_or_404
from django.core.cache import cache
from django.db.models import Count, Q, Case, When, F, Value, IntegerField, Exists, OuterRef, Subquery
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from products.documents import ProductDocument
from utils import utils
from utils.product_data import ProductSave
from utils.selenium_driver import SeleniumDriver
from utils.youtube_api import Youtube
from .serializers import *
from utils.utils import get_all_children
from .shema import shema
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import connection
from django.http import JsonResponse
from elasticsearch_dsl import Q, A, InnerDoc, Search
from elasticsearch_dsl.connections import connections
from bs4 import BeautifulSoup

from .models import ProductModel, ProductSearchHistoryModel

es_client = connections.get_connection()

# Create your views here.
class ProductsView(viewsets.ModelViewSet):
    serializer_class = ProductsSerializer
    model = ProductModel
    paginator = PageNumberPagination()

    def get_queryset(self):
        base_query = self.model.objects.filter(is_deleted=False)
        
        return base_query.filter(shop__is_active=True)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Product ID'),
        openapi.Parameter('start_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Start Date'),
        openapi.Parameter('end_date', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='End Date')
    ])
    def get_price_history(self, request):
        product_id = request.GET.get('product_id', None)
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        # Kullanıcı kendi mağazasının ürünlerini görebilmeli
        if request.user.is_authenticated and hasattr(request.user, 'shop'):
            products = ProductModel.objects.filter(id=product_id, shop=request.user.shop).first()
        else:
            products = ProductModel.objects.filter(id=product_id, shop__is_active=True).first()

        if products is None:
            return Response({'success': False, 'data': []})

        query = products.price_history.filter(is_deleted=False)

        if start_date and end_date:
            query = query.filter(updated_at__gte=start_date, updated_at__lte=end_date)
        datas = ProductPriceSerializer(query, many=True).data

        return Response({'success': True, 'data': datas})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size'), ])
    def populer_products(self, request):
        try:
            page_size = int(request.GET.get('page_size', 10))
            hex = f'populer_products_{page_size}'
            data = cache.get(hex)
            if data is not None:
                return Response({'success': True, 'data': data})

            # Kullanıcı kendi mağazasının ürünlerini görebilmeli
            shop_filter = {}
            if request.user.is_authenticated and hasattr(request.user, 'shop'):
                shop_filter = {'product__shop': request.user.shop}
            else:
                shop_filter = {'product__shop__is_active': True}

            # Get top products based on events
            top_products = (
                ProductEventModel.objects
                .filter(
                    product__is_deleted=False,
                    is_deleted=False,
                    **shop_filter
                )
                .values('product_id')
                .annotate(event_count=Count('product_id'))
                .order_by('-event_count')[:page_size]
                .values_list('product_id', flat=True)
            )

            # Get product details with shop filter
            shop_product_filter = {}
            if request.user.is_authenticated and hasattr(request.user, 'shop'):
                shop_product_filter = {'shop': request.user.shop}
            else:
                shop_product_filter = {'shop__is_active': True}

            products = (
                ProductModel.objects
                .filter(
                    id__in=top_products,
                    is_deleted=False,
                    **shop_product_filter
                )
                .select_related('shop', 'brand')
                .prefetch_related('category')
                .all()
            )

            serializer = ProductsElasticSerializer(products, many=True)
            cache.set(hex, serializer.data, timeout=3600)
            
            return Response({'success': True, 'data': serializer.data})

        except Exception as e:
            return Response(
                {'success': False, 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        responses={
            200: openapi.Response('Success response', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'data': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'active_products': openapi.Schema(type=openapi.TYPE_INTEGER, description='Count of active products'),
                            'products_count_passive': openapi.Schema(type=openapi.TYPE_INTEGER, description='Count of passive products'),
                            'video_url_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Count of products with video URLs'),
                            'match_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Count of product matches')
                        }
                    )
                }
            )),
            500: 'Internal Server Error'
        }
    )
    def general_info(self, request):
        # Kullanıcı kendi mağazasının ürünlerini görebilmeli
        if request.user.is_authenticated and hasattr(request.user, 'shop'):
            shop_filter = {'shop': request.user.shop}
        else:
            shop_filter = {'shop__is_active': True}

        products_count_active = ProductModel.objects.filter(is_deleted=False, **shop_filter).count()
        products_count_passive = ProductModel.objects.filter(is_deleted=True, **shop_filter).count()
        video_url_count = ProductModel.objects.filter(video_url__isnull=False, **shop_filter).count()

        match_query = 'SELECT COUNT(id) FROM products_match'
        match_count = 0
        with connection.cursor() as cursor:
            cursor.execute(match_query)
            results = cursor.fetchone()
            match_count = results[0]

        data = {
            'active_products': products_count_active,
            'products_count_passive': products_count_passive,
            'video_url_count': video_url_count,
            'match_count': match_count
        }
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[])
    def highlight_products(self, request):
        hex = f'highlight_products'
        data = cache.get(hex)
        if data is not None:
            return Response({'success': True, 'data': data})

        # Kullanıcı kendi mağazasının ürünlerini görebilmeli
        if request.user.is_authenticated and hasattr(request.user, 'shop'):
            products = ProductModel.objects.filter(
                is_deleted=False,
                shop=request.user.shop
            ).order_by('updated_at')[:6]
        else:
            products = ProductModel.objects.filter(
                is_deleted=False,
                shop__is_active=True
            ).order_by('updated_at')[:6]

        response = products
        serializer = ProductsElasticSerializer(response, many=True)
        cache.set(hex, serializer.data, timeout=3600)
        return Response({'success': True, 'data': serializer.data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('ids', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='ids'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('shop', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        ids = request.GET.get('ids', None)
        shop = request.GET.get('shop', None)
        category_name = request.GET.get('category_name', None)

        # Get base queryset based on authentication status
        base_query = self.get_queryset()

        if id_ is not None:
            #response = get_object_or_404(base_query, pk=id_)
            response = ProductModel.objects.filter(id=id_).first()
            return Response({'success': True, 'data': ProductsDetailSerializer(response).data})
        elif ids is not None:
            data = cache.get(f'last_products{ids}')
            if data is None:
                response = base_query.filter(id__in=ids.split(',')).all()
                data = ProductsElasticSerializer(response, many=True).data
                cache.set(f'last_products{ids}', data, 3600)
            return Response({'success': True, 'data': data})
        elif shop is not None:
            response = base_query.filter(shop=shop).all()
            self.paginator.page_size = page_size
            result_page = self.paginator.paginate_queryset(response, request)
            serializers = ProductsElasticSerializer(result_page, many=True)
            data = self.paginator.get_paginated_response(serializers.data).data
            return Response({'success': True, 'data': data})
        else:
            # Tüm ürünleri al
            base_query = base_query.filter(is_deleted=False)
            
            if category_name is not None:
                instance = CategoriesModel.objects.filter(is_deleted=False, name=category_name, shop=None).first()
                if instance is not None:
                    base_query = base_query.filter(category=instance)

            # Skorlara göre sırala
            products = base_query.order_by(
                '-final_score',  # Önce toplam puana göre
                '-updated_at'    # Sonra güncelleme tarihine göre
            )

            self.paginator.page_size = page_size
            result_page = self.paginator.paginate_queryset(products, request)
            
            if category_name is not None:
                serializers = ProductsElasticSerializer(result_page, many=True)
            else:
                serializers = self.serializer_class(result_page, many=True)
                
            data = self.paginator.get_paginated_response(serializers.data).data
            return Response({'success': True, 'data': data})

    def complex_data_serializer(self, obj):
        """ Custom serialization for complex types. """
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()  # Assuming complex objects have a to_dict() method
        raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('url', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='url')])
    def get_url_product(self, request):

        url = request.GET.get('url', None)
        decoded_url = base64.b64decode(url).decode('utf-8')
        selenium = SeleniumDriver()
        product_save = ProductSave()
        if 'amazon.com' in decoded_url or 'hepsiburada' in decoded_url:
            drive = selenium.driver_self(remote=True)
            drive.get(decoded_url)
            page_source = drive.page_source
        else:
            requests = cloudscraper.create_scraper()
            page_source = requests.get(decoded_url)
            page_source = page_source.text

        soup = BeautifulSoup(page_source, 'html.parser')
        name = soup.find('title')
        name = name.text if name else ''

        must = [
            {"term": {"is_deleted": False}},
            {"term": {"is_match": False}},
            {"term": {"shop.is_active": True}},
            Q('exists', field='image')
        ]

        #name = name.split('-')
        search_term = name
        #brand = name[0].strip()
        data = {'name': search_term.strip(), 'url': decoded_url}
        #must.append({"term": {"brand__name": brand}})
        main_query_2 = Q("match", name=search_term)
        #main_query_1 = Q("match", brand__name=brand)
        search = ProductDocument.search().query("bool", must=main_query_2, filter=must)
        # Sadece aktif mağazaların ürünlerini göstermek için filtre ekliyoruz
        search = search.filter("term", **{"shop.is_active": True})
        response = search.execute()

        same = []
        same_like = []
        like = []
        for hit in response:
            _score = hit.meta.score
            new_score = (_score / response.hits.max_score) * 100
            print(f'{new_score} - {hit.name}')
            if new_score  > 99.9:
                same.append(hit)
            elif new_score > 90:
                same_like.append(hit)
            else:
                like.append(hit)

        serializer_same = ProductsElasticSerializer(same, many=True).data
        serializer_same_like = ProductsElasticSerializer(same_like, many=True).data
        serializer_like = ProductsElasticSerializer(like, many=True).data
        sorted_products = sorted(serializer_same, key=lambda x: float(x["price"]))
        sorted_products_same_like = sorted(serializer_same_like, key=lambda x: float(x["price"]))
        return Response({'success': True, 'data': data,
                         'same':sorted_products,
                         'like':serializer_like,
                         'same_like':sorted_products_same_like})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='search'),
    ])
    def search_first_info(self, request):
        search_term = request.GET.get('search', None)
        if not search_term:
            return Response({'success': True, 'data': {
                'suggestions': [],
                'products': [],
                'categories': [],
                'brands': []
            }})

        # Log the search query
        try:
            # Save search history
            ProductSearchHistoryModel.objects.create(
                user=request.user if request.user.is_authenticated else None,
                search_term=search_term,
                search_type='search_first_info'
            )
        except Exception as e:
            print(f"Error logging search: {e}")

        # Clean and normalize search term
        original_search_term = search_term
        search_term = search_term.lower().strip()
        search_terms = search_term.split()  # Split into individual words for better matching
        
        # Define match types with explanations for clarity in results
        MATCH_TYPES = {
            'EXACT': 'Tam Eşleşme',        # Tam olarak aynı kelime/ifade
            'PARTIAL': 'Kısmi Eşleşme',    # Arama terimi ile başlayan kelimeler
            'PREFIX': 'Ön Ek Eşleşme',     # Kelimenin başlangıcı eşleşen
            'SIMILAR': 'Benzer Eşleşme',   # Yazım hatası olabilecek benzerlikler
            'RELATED': 'İlişkili Eşleşme'  # Birbiriyle ilişkili içerikler
        }

        # Türkçe karakter dönüşümleri için mapping (yazım hatası toleransı için)
        turkish_char_map = {
            'i': 'ı',
            'ı': 'i',
            'o': 'ö',
            'ö': 'o',
            'u': 'ü',
            'ü': 'u',
            'c': 'ç',
            'ç': 'c',
            's': 'ş',
            'ş': 's',
            'g': 'ğ',
            'ğ': 'g'
        }
        
        # Türkçe'ye özgü yazım alternatiflerini oluştur
        alternative_terms = [search_term]
        for i, char in enumerate(search_term):
            if char in turkish_char_map:
                alt_term = search_term[:i] + turkish_char_map[char] + search_term[i+1:]
                alternative_terms.append(alt_term)

        # ------ BRAND SEARCH QUERY ------
        brand_query = {
            "query": {
                "bool": {
                    "should": [
                        # Exact match with highest priority
                        {
                            "match_phrase": {
                                "name.keyword": {
                                    "query": search_term,
                                    "boost": 25  # Highest boost for exact match
                                }
                            }
                        },
                        # Prefix match with high priority
                        {
                            "prefix": {
                                "name.keyword": {
                                    "value": search_term,
                                    "boost": 20
                                }
                            }
                        },
                        # Term in any position with high boost
                        {
                            "wildcard": {
                                "name.keyword": {
                                    "value": f"*{search_term}*",
                                    "boost": 18
                                }
                            }
                        },
                        # Match each term in multi-term search
                        {
                            "multi_match": {
                                "query": search_term,
                                "fields": ["name^3", "name.ngram"],
                                "type": "best_fields",
                                "operator": "and",
                                "boost": 15
                            }
                        },
                        # Words in any order with medium priority
                        {
                            "match": {
                                "name": {
                                    "query": search_term,
                                    "fuzziness": 0,
                                    "operator": "and",
                                    "boost": 12
                                }
                            }
                        },
                        # Fuzzy match for handling typos
                        {
                            "match": {
                                "name": {
                                    "query": search_term,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2,
                                    "boost": 10
                                }
                            }
                        },
                        # Alternative terms for Turkish character sensitivity
                        *[{
                            "match": {
                                "name": {
                                    "query": alt_term,
                                    "boost": 8
                                }
                            }
                        } for alt_term in alternative_terms if alt_term != search_term],
                        # Individual term matches (for multi-word searches)
                        {
                            "terms": {
                                "name.keyword": search_terms,
                                "boost": 5
                            }
                        }
                    ],
                    "minimum_should_match": 1,
                    "filter": [
                        {"term": {"is_deleted": False}}
                    ]
                }
            },
            "size": 20,  # Get more results for better filtering
            "highlight": {
                "fields": {
                    "name": {}
                }
            },
            "aggs": {
                "popular_brands": {
                    "terms": {
                        "field": "name.keyword",
                        "size": 5
                    }
                }
            }
        }

        # ------ PRODUCT SEARCH QUERY ------
        product_query = {
            "query": {
                "bool": {
                    "should": [
                        # Exact product name match
                        {
                            "match_phrase": {
                                "name.keyword": {
                                    "query": search_term,
                                    "boost": 25
                                }
                            }
                        },
                        # Prefix match on product name
                        {
                            "prefix": {
                                "name.keyword": {
                                    "value": search_term,
                                    "boost": 20
                                }
                            }
                        },
                        # Term anywhere in name
                        {
                            "wildcard": {
                                "name.keyword": {
                                    "value": f"*{search_term}*",
                                    "boost": 18
                                }
                            }
                        },
                        # Multi-term matching on product name
                        {
                            "multi_match": {
                                "query": search_term,
                                "fields": ["name^3", "name.ngram"],
                                "type": "best_fields",
                                "operator": "and",
                                "boost": 15
                            }
                        },
                        # Brand matches (exact)
                        {
                            "match_phrase": {
                                "brand__name.keyword": {
                                    "query": search_term,
                                    "boost": 12
                                }
                            }
                        },
                        # Brand matches (prefix)
                        {
                            "prefix": {
                                "brand__name.keyword": {
                                    "value": search_term,
                                    "boost": 10
                                }
                            }
                        },
                        # Category matches
                        {
                            "match": {
                                "category_name": {
                                    "query": search_term,
                                    "boost": 8
                                }
                            }
                        },
                        # Barcode match
                        {
                            "term": {
                                "barcode": {
                                    "value": search_term,
                                    "boost": 25  # High priority for exact barcode match
                                }
                            }
                        },
                        # Fuzzy match with lower priority
                        {
                            "match": {
                                "name": {
                                    "query": search_term,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2,
                                    "boost": 5
                                }
                            }
                        },
                        # Alternative terms for Turkish character sensitivity
                        *[{
                            "match": {
                                "name": {
                                    "query": alt_term,
                                    "boost": 5
                                }
                            }
                        } for alt_term in alternative_terms if alt_term != search_term]
                    ],
                    "minimum_should_match": 1,
                    "filter": [
                        {"term": {"is_deleted": False}},
                        {"term": {"is_match": False}},
                        {"term": {"shop.is_active": True}},
                        {"exists": {"field": "image"}}
                    ]
                }
            },
            "_source": ["id", "name", "price", "image", "brand", "category_name", "barcode", "rating"],
            "size": 20,
            "highlight": {
                "fields": {
                    "name": {},
                    "brand__name": {},
                    "category_name": {}
                }
            }
        }

        # ------ CATEGORY SEARCH QUERY ------
        category_query = {
            "query": {
                "bool": {
                    "should": [
                        # Exact category match
                        {
                            "match_phrase": {
                                "name.keyword": {
                                    "query": search_term,
                                    "boost": 25
                                }
                            }
                        },
                        # Prefix match
                        {
                            "prefix": {
                                "name.keyword": {
                                    "value": search_term,
                                    "boost": 20
                                }
                            }
                        },
                        # Term anywhere in name
                        {
                            "wildcard": {
                                "name.keyword": {
                                    "value": f"*{search_term}*",
                                    "boost": 18
                                }
                            }
                        },
                        # Multi-term matching
                        {
                            "multi_match": {
                                "query": search_term,
                                "fields": ["name^3", "name.ngram", "parent.name"],
                                "type": "best_fields",
                                "operator": "and",
                                "boost": 15
                            }
                        },
                        # Words in any order
                        {
                            "match": {
                                "name": {
                                    "query": search_term,
                                    "operator": "and",
                                    "boost": 12
                                }
                            }
                        },
                        # Fuzzy match
                        {
                            "match": {
                                "name": {
                                    "query": search_term,
                                    "fuzziness": "AUTO",
                                    "prefix_length": 2,
                                    "boost": 8
                                }
                            }
                        },
                        # Alternative terms for Turkish character sensitivity
                        *[{
                            "match": {
                                "name": {
                                    "query": alt_term,
                                    "boost": 5
                                }
                            }
                        } for alt_term in alternative_terms if alt_term != search_term],
                        # Individual term matches
                        {
                            "terms": {
                                "name.keyword": search_terms,
                                "boost": 5
                            }
                        }
                    ],
                    "minimum_should_match": 1,
                    "filter": [
                        {"term": {"is_deleted": False}},
                        {"bool": {"must_not": {"exists": {"field": "shop"}}}}
                    ]
                }
            },
            "size": 20,
            "highlight": {
                "fields": {
                    "name": {}
                }
            }
        }

        # Execute queries against Elasticsearch
        brand_response = es_client.search(index='brands_index', body=brand_query)
        product_response = es_client.search(index='products_index', body=product_query)
        category_response = es_client.search(index='categories_index', body=category_query)

        # ------ PROCESS RESULTS ------
        
        # Process brand results
        brands = []
        if 'hits' in brand_response and 'hits' in brand_response['hits']:
            for hit in brand_response['hits']['hits']:
                source = hit['_source']
                brand_name = source.get('name', '').strip()
                
                # Determine match type
                match_type = MATCH_TYPES['SIMILAR']
                if brand_name.lower() == search_term:
                    match_type = MATCH_TYPES['EXACT']
                elif brand_name.lower().startswith(search_term):
                    match_type = MATCH_TYPES['PREFIX']
                elif any(brand_name.lower().startswith(term) for term in search_terms):
                    match_type = MATCH_TYPES['PARTIAL']
                
                # Extract highlight if available
                highlight = ''
                if 'highlight' in hit and 'name' in hit['highlight']:
                    highlight = ''.join(hit['highlight']['name'])
                
                # Add brand to results
                brands.append({
                    'id': hit['_id'],
                    'name': brand_name,
                    'score': hit['_score'],
                    'match_type': match_type,
                    'highlight': highlight
                })
        
        # Process category results
        categories = []
        if 'hits' in category_response and 'hits' in category_response['hits']:
            for hit in category_response['hits']['hits']:
                source = hit['_source']
                category_name = source.get('name', '').strip()
                category_slug = source.get('slug', '')
                
                # Determine match type
                match_type = MATCH_TYPES['SIMILAR']
                if category_name.lower() == search_term:
                    match_type = MATCH_TYPES['EXACT']
                elif category_name.lower().startswith(search_term):
                    match_type = MATCH_TYPES['PREFIX']
                elif any(category_name.lower().startswith(term) for term in search_terms):
                    match_type = MATCH_TYPES['PARTIAL']
                
                # Extract highlight if available
                highlight = ''
                if 'highlight' in hit and 'name' in hit['highlight']:
                    highlight = ''.join(hit['highlight']['name'])
                
                # Add category to results
                categories.append({
                    'id': hit['_id'],
                    'name': category_name,
                    'slug': category_slug,
                    'score': hit['_score'],
                    'match_type': match_type,
                    'highlight': highlight
                })
        
        # Process product results
        products = []
        if 'hits' in product_response and 'hits' in product_response['hits']:
            for hit in product_response['hits']['hits']:
                source = hit['_source']
                product_name = source.get('name', '').strip()
                
                # Determine match type
                match_type = MATCH_TYPES['SIMILAR']
                if product_name.lower() == search_term:
                    match_type = MATCH_TYPES['EXACT']
                elif product_name.lower().startswith(search_term):
                    match_type = MATCH_TYPES['PREFIX']
                elif any(product_name.lower().startswith(term) for term in search_terms):
                    match_type = MATCH_TYPES['PARTIAL']
                    
                # Brand ve category match kontrolü
                brand_name = source.get('brand', {}).get('name', '').lower()
                category_name = source.get('category_name', '').lower()
                
                if search_term in brand_name or any(term in brand_name for term in search_terms):
                    match_type = MATCH_TYPES['RELATED']
                elif search_term in category_name or any(term in category_name for term in search_terms):
                    match_type = MATCH_TYPES['RELATED']
                
                # Extract highlight if available
                highlight = ''
                if 'highlight' in hit:
                    if 'name' in hit['highlight']:
                        highlight = ''.join(hit['highlight']['name'])
                    elif 'brand__name' in hit['highlight']:
                        highlight = ''.join(hit['highlight']['brand__name'])
                    elif 'category_name' in hit['highlight']:
                        highlight = ''.join(hit['highlight']['category_name'])
                
                # Add product to results
                products.append({
                    'id': hit['_id'],
                    'name': product_name,
                    'price': source.get('price', 0),
                    'image': source.get('image', {}).get('thumb_file_url', ''),
                    'brand': source.get('brand', {}).get('name', ''),
                    'category': source.get('category_name', ''),
                    'score': hit['_score'],
                    'match_type': match_type,
                    'highlight': highlight,
                    'rating': source.get('rating', 0)
                })
        
        # ------ CREATE SUGGESTIONS ------
        
        all_suggestions = []
        suggestion_keys = {}  # To avoid duplicates
        
        # Process brands for suggestions (higher priority)
        for brand in sorted(brands, key=lambda x: x['score'], reverse=True):
            brand_key = brand['name'].lower()
            if brand_key not in suggestion_keys:
                suggestion_keys[brand_key] = True
                
                all_suggestions.append({
                    'text': brand['name'],
                    'type': 'brand',
                    'score': brand['score'],
                    'data': {
                        'id': brand['id'],
                        'name': brand['name'],
                        'highlight': brand.get('highlight', '')
                    },
                    'match_type': brand['match_type']
                })
        
        # Process categories for suggestions
        for category in sorted(categories, key=lambda x: x['score'], reverse=True):
            category_key = category['name'].lower()
            if category_key not in suggestion_keys:
                suggestion_keys[category_key] = True
                
                all_suggestions.append({
                    'text': category['name'],
                    'type': 'category',
                    'score': category['score'],
                    'data': {
                        'id': category['id'],
                        'name': category['name'],
                        'slug': category['slug'],
                        'highlight': category.get('highlight', '')
                    },
                    'match_type': category['match_type']
                })
        
        # Process products for suggestions
        for product in sorted(products, key=lambda x: x['score'], reverse=True):
            product_key = product['name'].lower()
            if product_key not in suggestion_keys:
                suggestion_keys[product_key] = True
                
                all_suggestions.append({
                    'text': product['name'],
                    'type': 'product',
                    'score': product['score'],
                    'data': {
                        'id': product['id'],
                        'name': product['name'],
                        'price': product['price'],
                        'image': product['image'],
                        'brand': product['brand'],
                        'category': product['category'],
                        'highlight': product.get('highlight', ''),
                        'rating': product.get('rating', 0)
                    },
                    'match_type': product['match_type']
                })
        
        # Add combination suggestions for multi-word searches
        if len(search_terms) > 1 and search_term not in suggestion_keys:
            # For example, if search is "c vitamin", add "C Vitamini" as a suggestion
            capitalized_terms = [term.capitalize() for term in search_terms]
            combined_suggestion = " ".join(capitalized_terms)
            combined_suggestion_key = combined_suggestion.lower()
            
            # Also try with Turkish variants (vitamin -> vitamini)
            turkish_variants = []
            if search_terms[-1] == "vitamin":
                turkish_variants.append(" ".join(search_terms[:-1] + ["vitamini"]))
            elif search_terms[-1] == "c" and len(search_terms) > 1:
                turkish_variants.append("C " + " ".join(search_terms[1:]))
            
            for variant in [combined_suggestion] + turkish_variants:
                variant_key = variant.lower()
                if variant_key not in suggestion_keys and variant_key != search_term:
                    suggestion_keys[variant_key] = True
                    all_suggestions.append({
                        'text': variant,
                        'type': 'combined',
                        'score': 12,  # Give a reasonable score
                        'data': {},
                        'match_type': MATCH_TYPES['RELATED']
                    })
        
        # Score and sort suggestions for final results
        def get_suggestion_score(suggestion):
            base_score = suggestion['score']
            text_lower = suggestion['text'].lower()
            
            # For multi-word searches, strongly penalize results that don't contain all terms
            if len(search_terms) > 1:
                missing_terms = 0
                for term in search_terms:
                    if term not in text_lower:
                        missing_terms += 1
                
                # If missing ANY terms for multi-word search, heavily penalize
                if missing_terms > 0:
                    # Penalize more severely for each missing term
                    penalty_factor = 0.1 ** missing_terms
                    base_score *= penalty_factor
            
            # Boost exact matches with higher multiplier
            if text_lower == search_term:
                base_score *= 50  # Increased from 30
            
            # Boost full containment (search term is fully contained in the suggestion)
            elif search_term in text_lower:
                base_score *= 35  # Increased from 20
                
            # Boost prefix matches with improved multiplier
            elif text_lower.startswith(search_term):
                base_score *= 15
            
            # Boost word-start matches with better multiplier
            elif any(word.startswith(search_term) for word in text_lower.split()):
                base_score *= 8
                
            # Check for partial word matches (e.g. "vit" matches "vitamin") - LOWER PRIORITY
            elif any(word.startswith(term) for word in text_lower.split() for term in search_terms):
                base_score *= 2
            
            # Check for reversed word order matches (e.g. "c vitamin" matches "vitamin c")
            elif search_terms and len(search_terms) > 1:
                reversed_terms = ' '.join(reversed(search_terms))
                if reversed_terms in text_lower:
                    base_score *= 15  # Increased from 10
            
            # Boost based on match type with improved weights
            match_type_boost = {
                MATCH_TYPES['EXACT']: 5.0,
                MATCH_TYPES['PREFIX']: 4.0,
                MATCH_TYPES['PARTIAL']: 3.0,
                MATCH_TYPES['RELATED']: 2.0,
                MATCH_TYPES['SIMILAR']: 1.5
            }
            match_type_multiplier = match_type_boost.get(suggestion['match_type'], 1.0)
            
            # Apply type multipliers for sorting with refined priorities
            type_multipliers = {
                'brand': 3.5,
                'category': 2.5,
                'combined': 3.0,
                'product': 1.5
            }
            
            # Enhanced rating boost for products
            rating_boost = 1.0
            if suggestion['type'] == 'product' and 'data' in suggestion:
                data = suggestion['data']
                
                # Rating boost
                if 'rating' in data and data['rating']:
                    rating = float(data['rating']) if isinstance(data['rating'], (int, float, str)) else 0
                    if rating > 0:
                        rating_boost = 1.0 + (rating / 5)
                
                # Price availability boost
                if 'price' in data and data['price']:
                    rating_boost *= 1.2
                
                # Image availability boost
                if 'image' in data and data['image']:
                    rating_boost *= 1.15
            
            # Length penalty: prefer short, precise matches
            length_penalty_factor = 0.015 if search_term in text_lower else 0.03
            length_penalty = 1.0 / (1 + len(text_lower) * length_penalty_factor)
            
            # Word count similarity: prefer suggestions with similar word count to search query
            search_word_count = len(search_terms)
            suggestion_word_count = len(text_lower.split())
            
            # If search is multi-word, prioritize multi-word suggestions
            if search_word_count > 1:
                if suggestion_word_count > 1:
                    word_count_similarity = 1.8  # Increased from 1.5
                else:
                    word_count_similarity = 0.2  # Decreased penalty from 0.5
            else:
                word_count_similarity = 1.0 / (1 + abs(search_word_count - suggestion_word_count) * 0.15)
            
            # Character overlap ratio - how many characters from search term appear in suggestion
            if search_term:
                common_chars = sum(1 for c in search_term if c in text_lower)
                char_overlap_ratio = common_chars / len(search_term)
                char_boost = 1.0 + (char_overlap_ratio * 0.8)
            else:
                char_boost = 1.0
            
            # Full term containment boost - significantly prioritize suggestions that contain the FULL search term
            full_term_boost = 1.0
            if search_term in text_lower:
                # Position boost - earlier appearance of search term is better
                position = text_lower.find(search_term)
                position_factor = 1.0 - (position / len(text_lower) * 0.5)
                full_term_boost = 8.0 * position_factor  # Increased from 5.0
            
            # Popularity boost (if available in data)
            popularity_boost = 1.0
            if suggestion['type'] == 'product' and 'data' in suggestion:
                if 'command_count' in suggestion['data']:
                    count = suggestion['data'].get('command_count', 0) or 0
                    popularity_boost = 1.0 + min(count / 100, 1.0)
            
            # Turkish language specific boosts
            turkish_boost = 1.0
            if any(special_char in text_lower for special_char in ['ı', 'ğ', 'ü', 'ş', 'ö', 'ç']):
                turkish_boost = 1.1
            
            return (
                base_score * 
                match_type_multiplier * 
                type_multipliers.get(suggestion['type'], 1.0) * 
                length_penalty *
                word_count_similarity *
                rating_boost *
                char_boost *
                popularity_boost *
                turkish_boost *
                full_term_boost
            )

        # Sort suggestions based on our advanced scoring function
        sorted_suggestions = sorted(all_suggestions, key=get_suggestion_score, reverse=True)

        # Add diversity to suggestions - mix different types
        def ensure_diversity(suggestions, max_suggestions=5):
            if len(suggestions) <= max_suggestions:
                return suggestions
                
            # Filter out results for multi-word searches more aggressively
            if len(search_terms) > 1:
                filtered_suggestions = []
                for s in suggestions:
                    text_lower = s['text'].lower()
                    
                    # For multi-word searches, require all terms to be present, or full phrase match
                    all_terms_present = all(term in text_lower for term in search_terms)
                    contains_full_query = search_term in text_lower
                    exact_match = text_lower == search_term
                    
                    if all_terms_present or contains_full_query or exact_match:
                        filtered_suggestions.append(s)
                
                # If we have filtered suggestions, use them; otherwise fall back to original
                if filtered_suggestions:
                    suggestions = filtered_suggestions
                else:
                    # As a fallback, at least require the first term
                    suggestions = [s for s in suggestions if search_terms[0] in s['text'].lower()]
                    
                    # If that gives us nothing, try the second term
                    if not suggestions and len(search_terms) > 1:
                        suggestions = [s for s in all_suggestions if search_terms[1] in s['text'].lower()]
                    
                    # Final fallback to original
                    if not suggestions:
                        suggestions = all_suggestions
            
            # Try to get at least one of each type if possible
            result = []
            type_counts = {'brand': 0, 'category': 0, 'product': 0, 'combined': 0}
            type_limits = {'brand': 2, 'category': 2, 'product': 1, 'combined': 1}
            
            for s in suggestions:
                s_type = s['type']
                if type_counts[s_type] < type_limits[s_type]:
                    result.append(s)
                    type_counts[s_type] += 1
                    
                if sum(type_counts.values()) >= max_suggestions:
                    break
                    
            # If we don't have enough suggestions yet, add more of any type
            remaining_slots = max_suggestions - sum(type_counts.values())
            if remaining_slots > 0:
                used_ids = {s['data'].get('id') for s in result if 'id' in s.get('data', {})}
                
                for s in suggestions:
                    if s not in result and s['data'].get('id') not in used_ids:
                        result.append(s)
                        used_ids.add(s['data'].get('id'))
                        remaining_slots -= 1
                        
                    if remaining_slots <= 0:
                        break
                        
            return result
            
        diverse_suggestions = ensure_diversity(sorted_suggestions)
        
        # Get top suggestions by type
        top_categories = sorted([c for c in categories], key=lambda x: x['score'], reverse=True)[:5]
        top_brands = sorted([b for b in brands], key=lambda x: x['score'], reverse=True)[:5]
        top_products = sorted(products, key=lambda x: x['score'], reverse=True)[:5]

        # Return final results with enhanced metadata
        return Response({
            'success': True,
            'data': {
                'suggestions': diverse_suggestions,             # Diverse mix of suggestions
                'products': top_products,                       # Top 5 products
                'categories': top_categories,                   # Top 5 categories
                'brands': top_brands,                           # Top 5 brands
                'query_info': {
                    'original_query': original_search_term,     # Original search query
                    'processed_query': search_term,             # Processed search query
                    'alternative_terms': alternative_terms,     # Alternative search terms considered
                    'total_results': len(brands) + len(categories) + len(products)
                }
            }
        })

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size'),
        openapi.Parameter('price_min', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='price_min'),
        openapi.Parameter('price_max', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='price_max'),
        openapi.Parameter('random', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='random'),
        openapi.Parameter('category_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_id'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('category_slug', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_slug'),
        openapi.Parameter('brand_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='brand_name'),
        openapi.Parameter('brand_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='brand_id'),
        openapi.Parameter('shop_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop_id'),
        openapi.Parameter('sort', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='sort'),
        openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='search')])
    def search(self, request):
        page_size = request.GET.get('page_size', 10)
        page = request.GET.get('page', 1)
        search_term = request.GET.get('search', None)
        search_params = ['name^4', 'brand__name^2', 'category_name^1', 'barcode^3']
        category_id = request.GET.get('category_id', None)
        category_filter = request.GET.get('category', None)
        category_name = request.GET.get('category_name', None)
        category_slug = request.GET.get('category_slug', None)
        brand_id = request.GET.get('brand_id', None)
        brand = request.GET.get('brand', None)
        shop_id = request.GET.get('shop_id', None)
        brand_name = request.GET.get('brand_name', None)
        random_ = request.GET.get('random', False)
        price = request.GET.get('price', None)
        order = request.GET.get('sort', None)
        is_match = request.GET.get('is_match', False)
        category = None

        # Log the search query if search term exists
        if search_term:
            try:
                # Save search history
                ProductSearchHistoryModel.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    search_term=search_term,
                    search_type='search'
                )
            except Exception as e:
                print(f"Error logging search: {e}")

        if brand_id == '':
            brand_id = None

        if brand is not None:
            print(brand)
            brand_id = brand
        brand_array = []
        must = [
            {"term": {"is_deleted": False}},
            Q('exists', field='image'),
            {"term": {"shop.is_active": True}}
        ]

        if is_match == False or is_match==True:
            must.append({"term": {"is_match": is_match}})

        for item in request.GET:
            try:
                val = request.GET.get(item).split(',')
                spect = SpecValueModel.objects.filter(id=item).first()
                if spect:
                    must.append(Q("terms", spec_values__id=val))
            except:
                pass

        if shop_id is not None:
            must.append({"term": {"shop.id": shop_id}})

        bread_crumb = []

        if category_slug is not None:
            category = CategoriesModel.objects.filter(slug=category_slug, is_deleted=False,
                                                      shop__isnull=True).first()
            if category is not None:
                category_id = category.id

        if category_name is not None:
            category = CategoriesModel.objects.filter(name=category_name, is_deleted=False).first()
            if category is not None:
                category_id = category.id

        if category_id is not None:
            hex = f'search_category_child{category_id}'
            ids = cache.get(hex)
            if ids is None:
                if category is None:
                    category = CategoriesModel.objects.filter(id=category_id, is_deleted=False).first()
                if category is not None:
                    children = get_all_children(category)
                    ids = [child.id for child in children]
                    ids.append(category.id)
                    cache.set(hex, ids, timeout=3600)
                    must.append(Q("terms", category__id=ids))
            else:
                must.append(Q("terms", category__id=ids))

        if brand_name is not None:
            brand_arr = brand_name.replace(' ', '').split(',')
            brand_instance = BrandModel.objects.filter(name__in=brand_arr, is_deleted=False).all()
            brand_ids = [child.id for child in brand_instance]
            if len(brand_ids) > 0:
                must.append(Q("terms", brand__id=brand_ids))

        if brand_id is not None and brand_name is None:
            brand_arr = brand_id.replace(' ', '').split(',')
            must.append(Q("terms", brand__id=brand_arr))

        #filters
        if category_filter is not None:
            category_filter = category_filter.split(',')
            must.append(Q("terms", category__id=category_filter))

        query_array = []
        if search_term:

            main_query_1 = Q("multi_match", query=search_term, fields=search_params)
            main_query_2 = Q("match", name=search_term)
            query_array.append(main_query_1)
            query_array.append(main_query_2)
        else:
            main_query = Q("match_all")
            query_array.append(main_query)

        if price is not None:
            price = price.split(',')
            must.append(Q("range", price={"gte": price[0], "lte": price[1]}))

        if order is None:
            if random_:
                order = 'final_score'
            else:
                if search_term:
                    order = '_score'
                else:
                    order = 'final_score'


        combined_query = Q('bool', must=query_array)
        print(combined_query)
        print(must)
        print(order)
        search = ProductDocument.search().query("bool", must=combined_query, filter=must)
        # Sadece aktif mağazaların ürünlerini göstermek için filtre ekliyoruz
        search = search.filter("term", **{"shop.is_active": True})
        page = int(page)
        page_size = int(page_size)
        offset = (page - 1) * page_size

        search = search.extra(size=page_size, from_=offset)
        search = search.sort(order)
        response = search.execute()

        if random_:
            hits = list(response.hits)
            random.shuffle(hits)
            subset_size = min(len(hits), page_size)
            random_subset = hits[:subset_size]
            response = random_subset

        try:
            count = search.count()
        except:
            count = 0

        if count == 0 and category_id is None:
            print(search_term)
            print(search_params)
            if search_term is None:
                main_query = Q()
            else:
                main_query = Q("multi_match", query=search_term, fields=search_params, fuzziness="AUTO")
            search = ProductDocument.search().query("bool", must=must, filter=main_query)
            # Sadece aktif mağazaların ürünlerini göstermek için filtre ekliyoruz
            search = search.filter("term", **{"shop.is_active": True})
            search = search.extra(size=page_size, from_=page)
            search = search.sort(order)
            response = search.execute()
            count = search.count()
        serializer = ProductsElasticSerializer(response, many=True).data
        data = {'success': True,
                'data': serializer,
                'total': count,
                'breadcrumb': bread_crumb}

        return Response(data)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size'),
        openapi.Parameter('category_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_id'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('category_slug', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_slug'),
        openapi.Parameter('shop', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop'),
        openapi.Parameter('brand_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='brand_name')])
    def main_page(self, request):
        page_size = request.GET.get('page_size', 10)
        page = request.GET.get('page', 1)

        category_id = request.GET.get('category_id', None)
        category_name = request.GET.get('category_name', None)
        category_slug = request.GET.get('category_slug', None)
        brand_name = request.GET.get('brand_name', None)
        shop = request.GET.get('shop', None)

        hex = f'main_page_{category_id}{category_name}{brand_name}{shop}{page}{page_size}'
        data = cache.get(hex)

        if data is not None:
            serializer = ProductsElasticSerializer(data, many=True).data
            data = {'success': True, 'data': serializer}
            return Response(data)

        must = [
            {"term": {"is_deleted": False}},
            {"term": {"is_match": False}},
            Q('exists', field='image'),
            {"term": {"shop.is_active": True}}
        ]

        if shop is not None:
            must.append({"term": {"shop.id": shop}})

        if category_name is not None:
            category = CategoriesModel.objects.filter(name=category_name, is_deleted=False).first()
            if category is not None:
                category_id = category.id

        if category_slug is not None:
            category = CategoriesModel.objects.filter(slug=category_slug, is_deleted=False,
                                                      shop__isnull=True).first()
            if category is not None:
                category_id = category.id

        if category_id is not None:
            category = CategoriesModel.objects.filter(id=category_id, is_deleted=False).first()
            children = get_all_children(category)
            ids = [child.id for child in children]
            category_filter = [{'id': category.id, 'label': category.name, 'slug': category.slug}]
            for child in children:
                category_filter.append({'id': child.id, 'label': child.name, 'slug': child.slug})
            ids.append(category.id)
            must.append(Q("terms", category__id=ids))

        if brand_name is not None:
            brand_instance = BrandModel.objects.filter(name=brand_name, is_deleted=False).first()
            if brand_instance is not None:
                must.append(Q("term", brand__id=brand_instance.id))

        query_array = []
        main_query = Q("match_all")
        query_array.append(main_query)
        order = '-final_score'
        combined_query = Q('bool', must=query_array)
        print(must)
        print(combined_query)
        search = ProductDocument.search().query("bool", must=combined_query, filter=must)
        # Sadece aktif mağazaların ürünlerini göstermek için filtre ekliyoruz
        search = search.filter("term", **{"shop.is_active": True})
        page = int(page)
        page_size = int(page_size)
        offset = (page - 1) * page_size

        search = search.extra(size=page_size, from_=offset)
        search = search.sort(order)
        response = search.execute()

        data_json = response
        cache.set(hex, data_json, timeout=3600)

        serializer = ProductsElasticSerializer(response, many=True).data
        data = {'success': True, 'data': serializer}

        return Response(data)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size'),
        openapi.Parameter('category_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_id'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('category_slug', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_slug'),
        openapi.Parameter('shop', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop'),
        openapi.Parameter('brand_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='brand_name')])
    def main_page(self, request):
        page_size = request.GET.get('page_size', 10)
        page = request.GET.get('page', 1)

        category_id = request.GET.get('category_id', None)
        category_name = request.GET.get('category_name', None)
        category_slug = request.GET.get('category_slug', None)
        brand_name = request.GET.get('brand_name', None)
        shop = request.GET.get('shop', None)

        hex = f'main_page_{category_id}{category_name}{brand_name}{shop}{page}{page_size}'
        data = None #cache.get(hex)

        if data is not None:
            serializer = ProductsElasticSerializer(data, many=True).data
            data = {'success': True, 'data': serializer}
            return Response(data)

        must = [
            {"term": {"is_deleted": False}},
            {"term": {"is_match": False}},
        ]

        if shop is not None:
            must.append({"term": {"shop.id": shop}})

        if category_name is not None:
            category = CategoriesModel.objects.filter(name=category_name, is_deleted=False).first()
            if category is not None:
                category_id = category.id

        if category_slug is not None:
            category = CategoriesModel.objects.filter(slug=category_slug, is_deleted=False,
                                                      shop__isnull=True).first()
            if category is not None:
                category_id = category.id
        if category_id is not None:
            category = CategoriesModel.objects.filter(id=category_id, is_deleted=False).first()
            children = get_all_children(category)
            ids = [child.id for child in children]
            category_filter = [{'id': category.id, 'label': category.name, 'slug': category.slug}]
            for child in children:
                category_filter.append({'id': child.id, 'label': child.name, 'slug': child.slug})
            ids.append(category.id)
            must.append(Q("terms", category__id=ids))

        if brand_name is not None:
            brand_instance = BrandModel.objects.filter(name=brand_name, is_deleted=False).first()
            if brand_instance is not None:
                must.append(Q("term", brand__id=brand_instance.id))

        query_array = []
        main_query = Q("match_all")
        query_array.append(main_query)
        order = '-final_score'
        combined_query = Q('bool', must=query_array)
        print(must)
        print(combined_query)
        search = ProductDocument.search().query("bool", must=combined_query, filter=must)
        page = int(page)
        page_size = int(page_size)
        offset = (page - 1) * page_size

        search = search.extra(size=page_size, from_=offset)
        search = search.sort(order)
        response = search.execute()
        print('****7')

        data_json = response
        cache.set(hex, data_json, timeout=3600)
        print('****8')
        serializer = ProductsElasticSerializer(response, many=True).data
        print('****9')
        data = {'success': True, 'data': serializer}

        return Response(data)

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def discounted(self, request):
        page = request.GET.get('page', 1)
        page_size = request.GET.get('page_size', 10)
        hex = f'discounted{page}{page_size}'
        data = cache.get(hex)
        if data is not None:
            return Response({'success': True, 'data': data})

        response = ProductDiscountModel.objects.filter(is_deleted=False, product__is_deleted=False).order_by(
            '-updated_at').all()
        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = ProductDiscountSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data
        cache.set(hex, data, timeout=3600)
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(request_body=shema['ProductsView']['favorite'])
    def favorite(self, request):
        product = request.data.get('product_id', None)
        user = request.user

        instance = ProductModel.objects.get(id=product)
        is_exist = ProductFavoriteModel.objects.filter(is_deleted=False, product=instance, user=user).first()
        if is_exist:
            is_exist.is_deleted = True
            is_exist.save()
        else:
            ProductFavoriteModel.objects.create(product=instance, user=user)
        return Response({'success': True})

    @swagger_auto_schema(request_body=shema['ProductsView']['rate'])
    def addUserListViewProduct(self, request):
        product = request.data.get('product_id', None)
        user = request.user

        instance = ProductModel.objects.get(id=product)
        rate_instance = ProductRateModel.objects.create(user=user)
        instance.rate.add(rate_instance)
        return Response({'success': True})

    @swagger_auto_schema(request_body=shema['ProductsView']['favorite'])
    def price_alarm(self, request):
        product = request.data.get('product_id', None)
        user = request.user

        instance = ProductModel.objects.get(id=product)
        is_exist = ProductPriceAlarmModel.objects.filter(is_deleted=False, product=instance, user=user).first()
        if is_exist:
            is_exist.is_deleted = True
            is_exist.save()
        else:
            ProductPriceAlarmModel.objects.create(product=instance,price=instance.price, user=user)
        return Response({'success': True})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def get_price_alarm(self, request):
        page_size = request.GET.get('page_size', 10)
        user = request.user
        if user.id is None:
            response = (ProductPriceAlarmModel.objects
                        .filter(is_deleted=False, product__is_deleted=False, user=None)
                        .order_by('updated_at').all())
        else:
            response = (ProductPriceAlarmModel.objects
                        .filter(is_deleted=False, product__is_deleted=False, user=user)
                        .order_by('updated_at').all())

        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = ProductFavoriteSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def get_favorite(self, request):
        page_size = request.GET.get('page_size', 10)
        user = request.user
        if user.id is None:
            response = (ProductFavoriteModel.objects
                        .filter(is_deleted=False, product__is_deleted=False, user=None)
                        .order_by('updated_at').all())
        else:
            response = (ProductFavoriteModel.objects
                        .filter(is_deleted=False, product__is_deleted=False, user=user)
                        .order_by('updated_at').all())

        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = ProductFavoriteSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('category_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='category_id'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def categories_products(self, request):
        page_size = request.GET.get('page_size', 10)
        category_id = request.GET.get('category_id', None)
        category_name = request.GET.get('category_name', None)

        if category_name is not None:
            category = CategoriesModel.objects.filter(name=category_name, is_deleted=False, shop=None).first()
            category_id = category.id

        if category_id is not None:
            category = CategoriesModel.objects.filter(id=category_id, is_deleted=False).first()
            children = get_all_children(category)
            ids = [child.id for child in children]
            ids.append(category.id)
            response = self.model.objects.filter(is_deleted=False, category__in=ids).all()
        else:
            response = self.model.objects.filter(is_deleted=False).all()

        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = ProductsElasticSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='category_id'),
        openapi.Parameter('link', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name')])
    def product_click(self, request):

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # X-Forwarded-For can contain multiple IPs, take the first one
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        product_id = request.GET.get('product_id', None)
        link = request.GET.get('link', None)
        user = request.user
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        user_agent = parse(user_agent_string)
        browser = user_agent.browser.family
        browser_version = user_agent.browser.version_string
        os_family = user_agent.os.family
        os_version = user_agent.os.version_string
        device = user_agent.device.family

        serializer = ProductSaveEventSerializer(data={'product': product_id, 'ip': ip})
        serializer.is_valid(raise_exception=True)
        if serializer.is_valid():
            instance = serializer.save()
            user = request.user if request.user.is_authenticated else None
            click_instance = ProductUserClickModel.objects.create(user=user,
                                                                  ip=ip,
                                                                  browser=browser,
                                                                  browser_version=browser_version,
                                                                  os_family=os_family,
                                                                  os_version=os_version,
                                                                  device=device)
            instance.click.add(click_instance)

        decoded_bytes = base64.b64decode(link)
        try:
            decoded_string = decoded_bytes.decode('utf-8')
            print(decoded_string)
        except:
            decoded_string = os.getenv('FRONTEND_URI')
        return redirect(decoded_string)
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('shop_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Shop ID'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Number of products per page'),
        openapi.Parameter('search_after_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='ID of the last product from the previous page')
    ])
    @action(detail=False, methods=['get'])
    def search_with_scroll(self, request):
        try:
            shop_id = request.query_params.get('shop_id')
            page_size = int(request.query_params.get('page_size', 24))
            search_after_id = request.query_params.get('search_after_id')
            
            s = Search(using=es_client, index='products_index')
            
            if shop_id:
                s = s.filter('term', **{'shop.id': int(shop_id)})
            
            # Sadece aktif mağazaların ürünlerini göstermek için filtre ekliyoruz
            s = s.filter('term', **{'shop.is_active': True})

            #toplam hits(toplam ürün sayısı)
            #page_size(her sayfadaki ürün sayısı)
            #search_after_id(son ürünün idsi)
            #next_search_after_id(sonraki sayfanın idsi)
            #has_more(sonraki sayfa var mı)
            #total(toplam ürün sayısı)
            #total_pages(toplam sayfa sayısı

            total_hits = s.count()
            total_pages = math.ceil(total_hits / page_size)
            
            s = s.sort('id')
            
            if search_after_id:
                s = s.extra(search_after=[int(search_after_id)])
            
            s = s.extra(size=page_size)
            
            response = s.execute()
            
            last_id = None
            if response.hits and len(response.hits) > 0:
                last_id = response.hits[-1].meta.id
            
            results = []
            for hit in response:
                hit_dict = hit.to_dict()
                product_dict = {
                    'id': hit.meta.id,
                    'title': hit_dict.get('name'),
                    'price': hit_dict.get('price'),
                    'shop_id': hit_dict.get('shop', {}).get('id'),
                    'is_match': hit_dict.get('is_match'),
                }
                results.append(product_dict)
            
            return Response({
                'results': results,
                'next_search_after_id': last_id,
                'has_more': len(response.hits) == page_size,
                'total': total_hits,
                'total_pages': total_pages
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ProductAuthView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ProductsSerializer
    model = ProductModel
    paginator = PageNumberPagination()

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, required=True, description='Product ID to get comments for'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Page number'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Number of comments per page')
    ])
    def get_comments(self, request):
        product_id = request.GET.get('product_id', None)
        page_size = request.GET.get('page_size', 10)
        
        if product_id is None:
            return Response({'success': False, 'message': 'Product ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = ProductModel.objects.get(id=product_id, is_deleted=False, shop__is_active=True)
            comments = product.product_comments.filter(is_deleted=False).order_by('-created_at')
            
            self.paginator.page_size = page_size
            result_page = self.paginator.paginate_queryset(comments, request)
            serializers = ProductCommentSerializer(result_page, many=True)
            data = self.paginator.get_paginated_response(serializers.data).data
            
            return Response({'success': True, 'data': data})
        except ProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Product not found'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=shema['ProductsView']['comment'],
        manual_parameters=[
            openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Product ID'),
            openapi.Parameter('comment', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Comment text')
        ],
        responses={
            200: openapi.Response('Success response', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def post_comment(self, request):
        product = request.data.get('product_id', None)
        comment_text = request.data.get('comment', None)
        user = request.user

        if not product or not comment_text:
            return Response({'success': False, 'message': 'Product ID and comment are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = ProductModel.objects.get(id=product, is_deleted=False)
            comment = ProductCommentModel.objects.create(
                user=user, 
                comment=comment_text,
                product=instance
            )
            instance.comment.add(comment)
            return Response({'success': True})
        except ProductModel.DoesNotExist:
            return Response({'success': False, 'message': 'Product not found'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'comment_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Comment ID'),
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description='Comment text')
            },
            required=['comment_id', 'comment']
        ),
        manual_parameters=[
            openapi.Parameter('comment_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Comment ID'),
            openapi.Parameter('comment', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='Comment text')
        ],
        responses={
            200: openapi.Response('Success response', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def put_comment(self, request):
        comment_id = request.data.get('comment_id', None)
        comment_text = request.data.get('comment', None)
        user = request.user

        if not comment_id or not comment_text:
            return Response({'success': False, 'message': 'Comment ID and comment text are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = ProductCommentModel.objects.get(id=comment_id, user=user, is_deleted=False)
            comment.comment = comment_text
            comment.save()
            return Response({'success': True})
        except ProductCommentModel.DoesNotExist:
            return Response({'success': False, 'message': 'Comment not found or you do not have permission'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=shema['ProductsView']['comment'],
        manual_parameters=[
            openapi.Parameter('comment_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Comment ID')
        ],
        responses={
            200: openapi.Response('Success response', schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                }
            )),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    def delete_comment(self, request):
        comment_id = request.data.get('comment_id', None)
        user = request.user

        if not comment_id:
            return Response({'success': False, 'message': 'Comment ID is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        try:
            comment = ProductCommentModel.objects.get(id=comment_id, user=user, is_deleted=False)
            comment.is_deleted = True
            comment.save()
            return Response({'success': True})
        except ProductCommentModel.DoesNotExist:
            return Response({'success': False, 'message': 'Comment not found or you do not have permission'}, 
                          status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(request_body=shema['ProductsView']['rate'])
    def rate(self, request):
        product = request.data.get('product_id', None)
        rate = request.data.get('rate', None)
        user = request.user

        instance = ProductModel.objects.get(id=product)
        rate_instance = ProductRateModel.objects.create(user=user, rate=rate)
        instance.rate.add(rate_instance)
        return Response({'success': True})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('ids', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='ids'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('order_by', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='order_by'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('shop', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop'),
        openapi.Parameter('rapor', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='rapor'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def product_list(self, request):
        # This endpoint is for authenticated shop owners to see their products
        if not request.user.shop:
            return Response({'success': False, 'message': 'No shop associated with user'}, 
                          status=status.HTTP_403_FORBIDDEN)

        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        ids = request.GET.get('ids', None)
        rapor = request.GET.get('rapor', False)
        order_by = request.GET.get('order_by', 'id')
        shop = request.user.shop.id

        # Shop owner can see all their own products regardless of shop status
        base_query = self.model.objects.filter(shop=shop)

        if id_ is not None:
            response = base_query.filter(id=id_).first()
            return Response({'success': True, 'data': ProductsDetailSerializer(response).data})
        elif ids is not None:
            data = cache.get(f'last_products{ids}')
            if data is None:
                response = base_query.filter(id__in=ids.split(','), shop=shop).order_by(order_by).all()
                data = ProductsMySerializer(response, many=True).data
                cache.set(f'last_products{ids}', data, 3600)
            return Response({'success': True, 'data': data})
        elif shop is not None:
            query = base_query.filter(shop=shop)  # Shop owner sees all their products
            if rapor:
                query = query.annotate(event_count=Count('event_product')).filter(event_count__gt=0)
            response = query.order_by(order_by).all()
            self.paginator.page_size = page_size
            result_page = self.paginator.paginate_queryset(response, request)
            serializers = ProductsMySerializer(result_page, many=True)
            data = self.paginator.get_paginated_response(serializers.data).data

            return Response({'success': True, 'data': data})
        else:
            if category_name is None:
                response = base_query.filter(is_deleted=False, shop=shop).order_by(order_by).all()
            else:
                hex = f'product_{category_name}'
                data = cache.get(hex)
                if data is not None:
                    response = data
                else:
                    instance = CategoriesModel.objects.filter(is_deleted=False, name=category_name, shop=None).first()
                    if instance is not None:
                        query = base_query.filter(is_deleted=False, category=instance, shop=shop)
                    else:
                        query = base_query.filter(is_deleted=False, shop=shop)
                    response = query.order_by(order_by).all()
                    cache.set(hex, response, timeout=3600)

            self.paginator.page_size = page_size
            result_page = self.paginator.paginate_queryset(response, request)
            if category_name is not None:
                serializers = ProductsElasticSerializer(result_page, many=True)
            else:
                serializers = self.serializer_class(result_page, many=True)
            data = self.paginator.get_paginated_response(serializers.data).data

            return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size'),
        openapi.Parameter('order_by', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='order_by'),
        openapi.Parameter('category_name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='category_name'),
        openapi.Parameter('shop', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='shop'),
        openapi.Parameter('rapor', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='rapor')])
    def product_event_list(self, request):
        page_size = request.GET.get('page_size', 10)
        order_by = request.GET.get('order_by', 'id')
        id_ = request.GET.get('id', None)
        query = ProductEventModel.objects
        if id_ is not None:
            query = query.filter(product=id_, is_deleted=False)

        response = query.order_by(order_by).all()
        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializer = ProductEventSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializer.data).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('search', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='search')])
    def youtube_video(self, request):
        search = request.GET.get('search', None)
        if search is None:
            return Response({'success': True, 'data': None})

        youtube = Youtube()
        video = youtube.search(search)
        return Response({'success': True, 'data': video})

class ProductPriceUpdateView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('product_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='Product ID')
    ])
    def get(self, request):
        product_scrapy = ProductSave()
        product_id = request.GET.get('product_id', None)
        if not product_id:
            return JsonResponse({'success': False, 'message': 'Product ID is required'},
                                status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(ProductModel, id=product_id)
        driver = product_scrapy.driver_self(True)
        # parent var mi?
        is_product = utils.parent_match(product.id)
        if is_product is not None:
            product = ProductModel.objects.filter(id=is_product).first()

        try:
            if product.match is not None:
                product_scrapy.get_updated_products(product, driver)
                for item in product.match.all():
                    product_scrapy.get_updated_products(item, driver)
            else:
                product_scrapy.get_updated_products(product, driver)
        except:
            driver.quit()
            return JsonResponse({'success': False})
        driver.quit()
        return JsonResponse({'success': True})