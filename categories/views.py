from django.core.cache import cache
import hashlib

from brands.serializers import BrandElasticSerializer
from categories.models import CategoriesModel
from categories.serializers import CategoriesSerializer, CategoriesChildSerializer, CategoriesMenuSerializer, \
    CategoriesDetailSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status, viewsets

from shops.models import ShopModel
from specs.models import SpecsModel
from specs.serializers import SpecSerialziers
from utils import utils
from rest_framework.permissions import IsAuthenticated
from .shema import shema
from utils.utils import get_all_children


# Create your views here.
class CategoriesView(viewsets.ModelViewSet):
    serializer_class = CategoriesSerializer
    model = CategoriesModel

    @swagger_auto_schema(manual_parameters=[])
    def get_all_child(self, request):
        data = cache.get('main_all_categories')
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),])
    def category_info(self, request):
        id_ = request.GET.get('id', None)
        category = CategoriesModel.objects.filter(id=id_).first()
        data = CategoriesDetailSerializer(category, many=False).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[])
    def categories_json(self, request):
        hex = 'main_menu_all_categories'
        data = cache.get(hex)
        if data is None:
            categories = CategoriesModel.objects.filter(is_deleted=False, shop__isnull=True).order_by('name')
            serializer = CategoriesMenuSerializer(categories, many=True)
            data = serializer.data
            cache.set(hex, data, timeout=60)
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='name'),
        openapi.Parameter('slug', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='slug'),
        openapi.Parameter('main', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='main'),
        openapi.Parameter('is_show_child', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='is_show_child'),
        openapi.Parameter('is_show_main', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='is_show_main'),
        openapi.Parameter('orderby', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='orderby'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        page = request.GET.get('page', 1)
        id_ = request.GET.get('id', None)
        name = request.GET.get('name', None)
        slug = request.GET.get('slug', None)
        parent = request.GET.get('parent', None)
        orderby = request.GET.get('orderby', 'id')
        main = request.GET.get('main', False)
        is_show_child = request.GET.get('is_show_child', 'false').lower() == 'true'
        is_show_main = request.GET.get('is_show_main', 'false').lower() == 'true'

        hex = utils.generate_cache_key(
            f'categories_{page_size}_{id_}_{parent}_{orderby}_{main}_{is_show_child}_{is_show_main}_{page}_{slug}_{name}')
        data = cache.get(hex)
        if data is not None:
            return Response({'success': True, 'data': data})

        if main == 'true':
            main = True

        if id_ is not None or slug is not None:
            if slug is not None:
                response = self.model.objects.filter(is_deleted=False, slug=slug).first()
            else:
                response = self.model.objects.filter(is_deleted=False, id=id_).first()
            if response is not None:
                children = response.get_children().order_by(orderby)
                children_data = self.serializer_class(children, many=True).data
            else:
                children_data = []
            return Response({'success': True,
                             'data': self.serializer_class(response, many=False).data,
                             'childeren': children_data})
        else:
            if main:
                query = self.model.objects.filter(is_deleted=False, parent=None, shop=None)
            elif is_show_main:
                query = self.model.objects.filter(is_deleted=False, shop=None)
            else:
                query = self.model.objects.filter(is_deleted=False)
            if name is not None:
                query = query.filter(name__icontains=name)
            response = query.order_by(orderby).all()

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        if is_show_child:
            serializers = CategoriesChildSerializer(result_page, many=True)
        else:
            serializers = self.serializer_class(result_page, many=True)

        data = paginator.get_paginated_response(serializers.data).data
        cache.set(hex, data, timeout=3600)
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('slug', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='slug'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def spec_list(self, request):
        id_ = request.GET.get('id', None)
        categories = self.model.objects.filter(is_deleted=False, id=id_).first()
        if categories is not None:
            all_specs = categories.specs.filter(is_deleted=False, is_active=True)
            spects = SpecSerialziers(all_specs, many=True).data
        else:
            spects = []
        return Response({'success': True, 'data': spects})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
    ])
    def category_filters(self, request):
        id = request.GET.get('id', None)

        category = CategoriesModel.objects.filter(id=id).first()
        brand_filters = []
        spect_filters = []
        if category is not None:
            hex = f'filters_{id}'
            datas = cache.get(hex)
            if datas is None:
                childerens = get_all_children(category)
                childerens.append(category)
                for child in childerens:
                    brands = child.brands.filter(is_deleted=False).all()
                    for brand in brands:
                        ser = BrandElasticSerializer(brand)
                        if ser.data not in brand_filters:
                            brand_filters.append(ser.data)
                    spects = child.specs.filter(is_deleted=False, is_active=True)
                    for spect in spects:
                        ser = SpecSerialziers(spect)
                        if ser.data not in spect_filters:
                            spect_filters.append(ser.data)

                serializer = CategoriesMenuSerializer(childerens, many=True)

                sorted_categories = sorted(serializer.data, key=lambda cat: cat['name'])
                sorted_brands = sorted(brand_filters, key=lambda cat: cat['name'])
                spect_filters = sorted(spect_filters, key=lambda spect: spect['name'])

                seen_names = set()
                unique_spect_filters = []

                for filter in spect_filters:
                    if filter['name'] not in seen_names:
                        unique_spect_filters.append(filter)
                        seen_names.add(filter['name'])

                datas = {'categories': sorted_categories,
                         'brand_filters':sorted_brands,
                         'spect_filters':unique_spect_filters}

                cache.set(hex, datas, timeout=21600)
        return Response({'success': True,
                         'categorie_filters': datas['categories'],
                         'brand_filters': datas['brand_filters'],
                         'spect_filters': datas['spect_filters']})


class CategoriesAuthView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategoriesSerializer
    model = CategoriesModel
    paginator = PageNumberPagination()

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        shop = request.user.shop.id
        response = self.model.objects.filter(is_deleted=False, parent=None, shop=shop).all()
        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = self.serializer_class(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(request_body=shema['CategoriesAuthView']['update_match'])
    def update_match(self, request):
        category_id = request.data.get('category_id', None)
        match = request.data.get('match', None)
        shop_id = request.user.shop.id
        shop = ShopModel.objects.get(pk=shop_id)
        instance = self.model.objects.filter(is_deleted=False, id=category_id, shop=shop).first()
        if instance is not None:
            instance_match = self.model.objects.filter(is_deleted=False, id=match, shop=None).first()
            if instance_match is not None:
                instance.match = instance_match
                instance.save()
        return Response({'success': True})