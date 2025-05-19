from django.utils.decorators import method_decorator

from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from drf_yasg.utils import swagger_auto_schema

from utils.decorators import superuser_required
from utils.utils import filters

from .serializers import MailSerializer
from .models import MailModel
from .shema import shema


class MailView(viewsets.ModelViewSet):
    permission_required = [IsAuthenticated]
    serializer_class = MailSerializer

    @swagger_auto_schema(manual_parameters=shema)
    @method_decorator(superuser_required, name='dispatch')
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)

        if id_ is not None:
            response = MailModel.objects.filter(is_deleted=False, id=id_).first()
            return Response({'success': True, 'data': self.get_serializer(response).data})
        else:
            response = MailModel.objects.filter(is_deleted=False)
            response = filters(request, response)

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        serializers = self.get_serializer(result_page, many=True)
        data = paginator.get_paginated_response(serializers.data).data

        return Response({'success': True, 'data': data})
