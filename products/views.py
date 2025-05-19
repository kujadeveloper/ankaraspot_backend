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
from bs4 import BeautifulSoup

from .models import ProductModel, ProductSearchHistoryModel


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