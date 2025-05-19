from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.http import Http404
from .models import BlogModel
from .serializers import BlogSerializer

class BlogListAPIView(APIView):
    """
    Tüm aktif blogları listeleyen API view.
    """
    @swagger_auto_schema(
        operation_summary="Blog Listesi",
        operation_description="Tüm aktif blogların listesini döndürür.",
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description="Sayfa numarası", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Sayfa başına gösterilecek blog sayısı", type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="Başarılı",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'title': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'content': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                            'slug': openapi.Schema(type=openapi.TYPE_STRING),
                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                            'status': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                        }
                    )
                )
            )
        }
    )
    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        
        start = (page - 1) * page_size
        end = start + page_size
        
        blogs = BlogModel.objects.filter(status=True).order_by('-created_at')[start:end]
        serializer = BlogSerializer(blogs, many=True)
        return Response({'data':serializer.data, 'success': True}, status=status.HTTP_200_OK)

class BlogDetailAPIView(APIView):
    """
    Belirtilen slug'a sahip blogun detayını döndüren API view.
    """
    @swagger_auto_schema(
        operation_summary="Blog Detay",
        operation_description="Belirtilen slug'a sahip blogun detay bilgisini döndürür.",
        responses={
            200: openapi.Response(
                description="Başarılı",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'title': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'content': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'slug': openapi.Schema(type=openapi.TYPE_STRING),
                        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                        'status': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                    }
                )
            ),
            404: openapi.Response(
                description="Blog bulunamadı",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request, slug):
        try:
            blog = BlogModel.objects.get(slug=slug, status=True)
        except BlogModel.DoesNotExist:
            return Response({"detail": "Blog not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = BlogSerializer(blog)
        return Response({'data':serializer.data, 'success': True}, status=status.HTTP_200_OK)


    