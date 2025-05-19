import uuid

from django.http import JsonResponse
from django.views.generic import View

from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from sitesettings.models import SitesettingsModels
from attachment.models import AttachmentModel
from attachment.serializers import AttachmentSerializer
from utils.s3 import S3, Cloud


class AttachmentView(viewsets.ModelViewSet):
    parser_classes = (FormParser, MultiPartParser)
    serializer_class = AttachmentSerializer

    @swagger_auto_schema(manual_parameters=[
        openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id'),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page'),
        openapi.Parameter('term', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='term'),
        openapi.Parameter('page_size', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='page_size')])
    def list(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        term = request.GET.get('term', None)

        if term is not None:
            response = AttachmentModel.objects.filter(is_deleted=False, id=term).first()
            results = [{'id': response.id, 'text': response.id}]  # Customize response format
            return JsonResponse({'results': results})
        if id_ is not None:
            response = AttachmentModel.objects.filter(is_deleted=False, id=id_).first()
            return Response({'success': True, 'data': AttachmentSerializer(response, many=False).data})
        else:
            response = AttachmentModel.objects.filter(is_deleted=False).all()

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        serializers = AttachmentSerializer(result_page, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('file', in_=openapi.IN_FORM, type=openapi.TYPE_FILE, description='file'),
        ],
        responses={200: openapi.Response('Description')}
    )
    def create(self, request):
        sitesettings = SitesettingsModels.objects.first()
        file = request.FILES.get('file')
        orj_filename = str(file)
        ext = orj_filename.split('.')[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        if sitesettings.cdn_systems == 0:
            s3 = S3()
            response_s3 = s3.send_file(file, filename, request.user.id)
        else:
            cloud = Cloud()
            response_s3 = cloud.upload_image_to_gcs(orj_filename, filename, file)

        serializers = AttachmentSerializer(
            data={'orjinal_file_url': response_s3, 'thumb_file_url': response_s3, 'name': filename,
                  'orjinal_name': orj_filename, 'user': request.user.id})
        serializers.is_valid(raise_exception=True)
        data = serializers.save()
        return Response(
            {'success': True, 'message': 'Kayıt oluşturuldu.', 'img': data.id, 'data': AttachmentSerializer(data).data})