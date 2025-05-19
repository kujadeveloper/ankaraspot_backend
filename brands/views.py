from rest_framework import viewsets

from brands.models import BrandModel
from brands.serializers import BrandSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status, viewsets

# Create your views here.
class BrandView(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    model = BrandModel
    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('is_main', openapi.IN_QUERY, type=openapi.TYPE_BOOLEAN, description='is_main'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        is_main = request.GET.get('is_main', 'false').lower() in ['true', '1', 'yes']
        id_ = request.GET.get('id', None)

        if id_ is not None:
            response = self.model.objects.filter(is_deleted=False, id=id_).first()
            return Response({'success': True, 'data': response})
        else:
            response = self.model.objects
            if is_main:
                response = response.filter(is_deleted=False, is_main=True).all()
            else:
                response = response.filter(is_deleted=False).all()
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        serializers = self.serializer_class(result_page, many=True)
        data = paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})