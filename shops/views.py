import requests

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from brands.models import BrandModel
from categories.models import CategoriesModel
from shops.models import ShopModel, ShopCommentModel, HtmlFieldModel
from shops.serializers import ShopPublicSerializer, ShopCommentSerializer, ShopHtmlSerializer
from .shema import shema
from utils.product_data import ProductSave
from bs4 import BeautifulSoup


# Create your views here.
class ShopViews(viewsets.ModelViewSet):
    serializer_class = ShopPublicSerializer
    model = ShopModel
    paginator = PageNumberPagination()

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('name', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='name'),
        openapi.Parameter('order', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='order'),
        openapi.Parameter('url', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='url'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        name = request.GET.get('name', None)
        url = request.GET.get('url', None)
        order = request.GET.get('order', 'id')

        if url is not None:
            #trendyol url varsa
            if 'trendyol' in url:
                url = 'https://transport.productsup'
            if 'a101' in url:
                url = 'https://a101-ecom.wawlabs.com/search?q={search}&rpp=6&pn={page}'
            response = ShopModel.objects.filter(url__icontains=url, is_active=True).first()
            return Response({'success': True, 'data': self.serializer_class(response, many=False).data})

        if id_ is not None:
            response = self.model.objects.filter(is_deleted=False, is_active=True, id=id_).first()
            return Response({'success': True, 'data': self.serializer_class(response, many=False).data})
        elif name is not None:
            # Tam eşleşen adı getir
            response = self.model.objects.filter(is_deleted=False, is_active=True, name=name).first()
            if response:
                return Response({'success': True, 'data': self.serializer_class(response, many=False).data})
            else:
                response = self.model.objects.filter(is_deleted=False, is_active=True).order_by(order).all()
        else:
            response = self.model.objects.filter(is_deleted=False, is_active=True).order_by(order).all()

        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = self.serializer_class(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def comment_lists(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)

        response = self.model.objects.filter(is_deleted=False, id=id_).first()
        response = response.comment.filter(is_deleted=False).all()
        self.paginator.page_size = page_size
        result_page = self.paginator.paginate_queryset(response, request)
        serializers = ShopCommentSerializer(result_page, many=True)
        data = self.paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('url', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='url'),
        openapi.Parameter('shop_id', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='url')])
    def get_url_data(self, request):
        product_save = ProductSave()
        url = request.GET.get('url', None)
        shop_id = request.GET.get('shop_id', None)

        shop = ShopModel.objects.filter(id=shop_id).first()
        if shop.sync_service==6:
            page_source = requests.get(url, headers=product_save.headers)
            page_source.encoding = 'utf-8'
            page_source = page_source.text
        else:
            driver = product_save.driver_self(True)
            driver.get(url)
            page_source = driver.page_source
            driver.quit()

        save_data = None
        if page_source is not None:
            soup = BeautifulSoup(page_source, 'html.parser')
            data = product_save.is_productv2(soup, shop)
            data['name'] = data['title']
            if 'brand' not in data:
                data['brand'] = 'diğer'
            if 'category' not in data:
                data['category'] = 'diğer'
            save_data = product_save.prepare_data(data, shop)

        category = CategoriesModel.objects.filter(id=save_data['category_id']).first()
        if category is not None:
            save_data['category'] = category.name

        brand = BrandModel.objects.filter(id=save_data['brand_id']).first()
        if brand is not None:
            save_data['brand'] = brand.name
        return Response({'success': True, 'data': save_data})

    @swagger_auto_schema(request_body=shema['ShopViews']['html_map'])
    def html_map_create(self, request):
        id_ = request.data.get('id', None)
        type = request.data.get('type', None)
        tag = request.data.get('tagName', None)
        tag_class = request.data.get('className', None)
        tag_id = request.data.get('tagId', None)
        tag_attr = request.data.get('attributes', None)
        text = request.data.get('text', None)
        order = request.data.get('order', 0)
        priority = request.data.get('priority', 0)

        shop = ShopModel.objects.filter(id=id_).first()
        serializer = ShopHtmlSerializer(data={'id': id_,
                                              'type': type,
                                              'tag': tag,
                                              'tag_class': tag_class,
                                              'tag_id':tag_id,
                                              'tag_attr':tag_attr,
                                              'text':text,
                                              'order':order,
                                              'priority':priority})
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        shop.html_map.add(instance)
        return Response({'success': True})

    @swagger_auto_schema(request_body=shema['ShopViews']['html_map_delete'])
    def html_map_delete(self, request):
        shop_id = request.data.get('shop_id', None)
        id_ = request.data.get('id', None)

        shop = ShopModel.objects.filter(id=shop_id).first()
        instance = HtmlFieldModel.objects.get(pk=id_)
        shop.html_map.remove(instance)
        return Response({'success': True})

class ShopAuthViews(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ShopPublicSerializer
    model = ShopModel

    @swagger_auto_schema(request_body=shema['ShopViews']['comment'])
    def comment(self, request):
        id_ = request.data.get('shop_id', None)
        comment = request.data.get('comment', None)
        user = request.user
        instance = ShopModel.objects.get(id=id_, is_deleted=False)
        print(user)
        comment = ShopCommentModel.objects.create(user=user, comment=comment)
        instance.comment.add(comment)
        return Response({'success': True})
