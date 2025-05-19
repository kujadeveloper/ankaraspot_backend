from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from specs.models import SpecsModel, SpecValueModel
from specs.serializers import SpecSerialziers, SpecValueSerialziers, SpecCreateSerializer
from shops.models import ShopModel
from dal import autocomplete
    
class SpecsView(viewsets.ModelViewSet):
    serializer_class = SpecSerialziers
    model = SpecsModel

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='id')])
    def get_spect_value(self, request):
        id_ = request.GET.get('id', None)
        instance = self.model.objects.get(pk=id_)
        values = instance.value.filter(is_deleted=False).order_by('value')
        datas = SpecValueSerialziers(values, many=True)
        return Response({'success': True, 'data': datas.data})

    @swagger_auto_schema(
        request_body=SpecCreateSerializer,
        responses={
            200: 'Başarılı - Mevcut özellik kullanıldı',
            201: 'Oluşturuldu - Yeni özellik oluşturuldu',
            400: 'Geçersiz İstek',
            404: 'Mağaza bulunamadı'
        }
    )
    def create_spec(self, request):
        try:
            serializer = SpecCreateSerializer(data=request.data)
            if serializer.is_valid():
                name = serializer.validated_data['name']
                shop_id = serializer.validated_data['shop']
                values = serializer.validated_data['value']
                product_id = serializer.validated_data.get('product_id')  # Ürün ID'sini al

                shop = get_object_or_404(ShopModel, id=shop_id)
                product = None
                if product_id:
                    product = get_object_or_404(ProductModel, id=product_id)

                existing_spec = self.model.objects.filter(
                    name=name,
                    shop=shop
                ).first()
                
                if existing_spec:
                    spec = existing_spec
                    status_code = status.HTTP_200_OK
                else:
                    spec = self.model.objects.create(
                        name=name,
                        shop=shop
                    )
                    status_code = status.HTTP_201_CREATED

                created_values = []
                for value in values:
                    existing_value = SpecValueModel.objects.filter(
                        shop=shop,
                        value=value,
                        is_deleted=False
                    ).first()

                    if existing_value:
                        spec_value = existing_value
                    else:
                        spec_value = SpecValueModel.objects.create(
                            shop=shop,
                            value=value,
                            specs=spec
                        )

                    if not spec.value.filter(id=spec_value.id).exists():
                        spec.value.add(spec_value)
                    
                    created_values.append(spec_value)

                    # Ürün varsa spec ve spec value'yu ekle
                    if product:
                        if not product.specs.filter(id=spec.id).exists():
                            product.specs.add(spec)
                        if not product.spec_values.filter(id=spec_value.id).exists():
                            product.spec_values.add(spec_value)

                return Response({
                    'success': True,
                    'message': 'Spec processed successfully',
                    'data': {
                        'id': spec.id,
                        'name': spec.name,
                        'values': [{'id': val.id, 'value': val.value} for val in created_values],
                        'is_new': status_code == status.HTTP_201_CREATED
                    }
                }, status=status_code)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
