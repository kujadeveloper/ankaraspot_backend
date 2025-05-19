from django.shortcuts import render
from django.db.models import Avg, Sum
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from products.models import ProductModel
from attachment.models import AttachmentModel
from .models import ShopComparisonModel
from .serializers import ShopComparisonSerializer
from .schemas import (
    shop_comparison_request,
    shop_comparison_response,
    shop_comparison_get_parameters,
    shop_comparison_get_response
)

class ShopComparisonView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ShopComparisonModel.objects.none()
        return ShopComparisonModel.objects.filter(product__shop=self.request.user.shop)
    
    @swagger_auto_schema(
        operation_description="Seçilen mağazaların ürünleri ile kullanıcının ürünlerini karşılaştırır.",
        request_body=shop_comparison_request,
        responses={
            200: openapi.Response(
                description="Başarılı karşılaştırma sonuçları",
                schema=shop_comparison_response
            ),
            400: 'Geçersiz istek',
            401: 'Yetkisiz erişim'
        }
    )
    def post(self, request):
        """Seçilen mağazaların ürünleri ile kullanıcı ürünlerini analiz eder."""
        if getattr(self, 'swagger_fake_view', False):
            return Response({})
            
        user = request.user
        shop_ids = request.data.get('shop_ids', [])
        
        if not shop_ids:
            return Response(
                {'error': 'En az bir mağaza seçmelisiniz'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if not hasattr(user, 'shop'):
            return Response(
                {'error': 'Kullanıcıya ait mağaza bulunamadı'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Kullanıcının mağazasındaki ürünleri ve eşleşmeleri tek sorguda al
            user_products = ProductModel.objects.filter(
                shop=user.shop,
                is_deleted=False,
                is_match=True
            ).values('id', 'price', 'shop_id', 'name', 'image', 'slug')
            
            # Eşleşen ürün ID'lerini al
            match_data = ProductModel.objects.filter(
                shop=user.shop,
                is_deleted=False,
                is_match=True
            ).values('id', 'match')
            
            # Eşleşme haritası oluştur
            match_map = {}
            for item in match_data:
                if item['id'] not in match_map:
                    match_map[item['id']] = set()
                if item['match']:
                    match_map[item['id']].add(item['match'])
            
            # Karşılaştırılacak ürünleri al
            competitor_products = ProductModel.objects.filter(
                shop_id__in=shop_ids,
                is_deleted=False,
                is_match=True
            ).values('id', 'price', 'shop_id', 'name', 'image', 'slug')
            
            # Görüntü ID'lerini topla
            image_ids = []
            for p in user_products:
                if p['image']:
                    image_ids.append(p['image'])
            
            # Görüntü URL'lerini al
            image_urls = {}
            if image_ids:
                attachments = AttachmentModel.objects.filter(
                    id__in=image_ids,
                    is_deleted=False
                ).values('id', 'thumb_file_url')
                
                image_urls = {a['id']: a['thumb_file_url'] for a in attachments}
            
            # Bulk işlem için liste oluştur
            comparison_updates = []
            
            # Ürünleri dictionary'e çevir
            competitor_dict = {p['id']: p for p in competitor_products}
            user_product_dict = {p['id']: p for p in user_products}
            
            for user_product in user_products:
                matched_ids = match_map.get(user_product['id'], set())
                
                for competitor_id in matched_ids:
                    competitor = competitor_dict.get(competitor_id)
                    if competitor and competitor['shop_id'] in shop_ids:
                        price_diff = user_product['price'] - competitor['price']
                        price_diff_percentage = (price_diff / competitor['price'] * 100) if competitor['price'] > 0 else 0
                        
                        comparison = ShopComparisonModel(
                            product_id=user_product['id'],
                            competitor_product_id=competitor['id'],
                            competitor_shop_id=competitor['shop_id'],
                            price_difference=price_diff,
                            price_difference_percentage=price_diff_percentage,
                            is_cheaper=price_diff < 0,
                            last_updated=timezone.now()
                        )
                        comparison_updates.append(comparison)
            
            # Önce mevcut karşılaştırmaları sil
            if comparison_updates:
                product_ids = [c.product_id for c in comparison_updates]
                competitor_shop_ids = [c.competitor_shop_id for c in comparison_updates]
                
                ShopComparisonModel.objects.filter(
                    product_id__in=product_ids,
                    competitor_shop_id__in=competitor_shop_ids
                ).delete()
                
                # Yeni karşılaştırmaları ekle
                ShopComparisonModel.objects.bulk_create(comparison_updates)
            
            # Sonuçları mağazalara göre grupla
            response_data = {}
            for shop_id in shop_ids:
                shop_analyses = [a for a in comparison_updates if a.competitor_shop_id == shop_id]
                
                analyses_data = []
                for analysis in shop_analyses:
                    user_product_info = user_product_dict.get(analysis.product_id, {})
                    image_id = user_product_info.get('image')
                    thumb_url = image_urls.get(image_id, '')
                    
                    competitor_info = competitor_dict.get(analysis.competitor_product_id, {})
                    
                    analyses_data.append({
                        'id': analysis.id,
                        'product_id': analysis.product_id,
                        'product_name': user_product_info.get('name', ''),
                        'product_image': thumb_url,
                        'product_slug': user_product_info.get('slug', ''),
                        'competitor_product_id': analysis.competitor_product_id,
                        'competitor_product_slug': competitor_info.get('slug', ''),
                        'competitor_shop_id': analysis.competitor_shop_id,
                        'price_difference': analysis.price_difference,
                        'price_difference_percentage': analysis.price_difference_percentage,
                        'is_cheaper': analysis.is_cheaper,
                        'last_updated': analysis.last_updated
                    })
                
                response_data[str(shop_id)] = {
                    'total_matched_products': len(shop_analyses),
                    'cheaper_products': len([a for a in shop_analyses if a.is_cheaper]),
                    'expensive_products': len([a for a in shop_analyses if not a.is_cheaper and a.price_difference != 0]),
                    'equal_price_products': len([a for a in shop_analyses if a.price_difference == 0]),
                    'total_price_difference': sum(a.price_difference for a in shop_analyses),
                    'avg_price_difference': sum(a.price_difference for a in shop_analyses) / len(shop_analyses) if shop_analyses else 0,
                    'analyses': analyses_data
                }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Mevcut karşılaştırma sonuçlarını getirir.",
        manual_parameters=shop_comparison_get_parameters,
        responses={
            200: openapi.Response(
                description="Başarılı",
                schema=shop_comparison_get_response
            ),
            400: 'Geçersiz istek',
            401: 'Yetkisiz erişim'
        }
    )
    def get(self, request):
        """Mevcut karşılaştırma sonuçlarını getirir."""
        if getattr(self, 'swagger_fake_view', False):
            return Response({})
            
        user = request.user
        shop_ids = request.GET.getlist('shop_ids[]', [])
        
        if not shop_ids:
            shop_ids = request.GET.getlist('shop_ids', [])
        
        try:
            shop_ids = [int(shop_id) for shop_id in shop_ids if shop_id]
        except ValueError:
            return Response(
                {'error': 'Geçersiz mağaza ID formatı'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not shop_ids:
            return Response(
                {'error': 'En az bir mağaza ID\'si gereklidir'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            analyses = self.get_queryset().filter(competitor_shop_id__in=shop_ids)
            
            response_data = {}
            for shop_id in shop_ids:
                shop_analyses = analyses.filter(competitor_shop_id=shop_id)
                
                # Only include data if analyses exist for this shop
                if shop_analyses.exists():
                    # Enrich the serialized data with product name and thumb URL
                    serialized_data = ShopComparisonSerializer(shop_analyses, many=True).data
                    
                    # Get all product IDs from the analyses
                    product_ids = [item.product_id for item in shop_analyses]
                    
                    # Fetch product data in one query
                    products = {
                        p.id: {'name': p.name, 'image': p.image, 'slug': p.slug}
                        for p in ProductModel.objects.filter(id__in=product_ids)
                    }
                    
                    # Get all competitor product IDs
                    competitor_product_ids = [item.competitor_product_id for item in shop_analyses]
                    
                    # Fetch competitor product data
                    competitor_products = {
                        p.id: {'slug': p.slug}
                        for p in ProductModel.objects.filter(id__in=competitor_product_ids)
                    }
                    
                    # Görüntü ID'lerini topla
                    image_ids = []
                    for product_id, product_data in products.items():
                        if product_data['image']:
                            image_ids.append(product_data['image'])
                    
                    # Görüntü URL'lerini al
                    image_urls = {}
                    if image_ids:
                        attachments = AttachmentModel.objects.filter(
                            id__in=image_ids,
                            is_deleted=False
                        ).values('id', 'thumb_file_url')
                        
                        image_urls = {a['id']: a['thumb_file_url'] for a in attachments}
                    
                    # Add product data to the serialized results
                    for item in serialized_data:
                        product_data = products.get(item['product_id'], {})
                        image_id = product_data.get('image')
                        thumb_url = image_urls.get(image_id, '')
                        
                        item['product_name'] = product_data.get('name', '')
                        item['product_image'] = thumb_url
                        item['product_slug'] = product_data.get('slug', '')
                        
                        competitor_product_data = competitor_products.get(item['competitor_product_id'], {})
                        item['competitor_product_slug'] = competitor_product_data.get('slug', '')
                    
                    response_data[str(shop_id)] = {
                        'total_matched_products': shop_analyses.count(),
                        'cheaper_products': shop_analyses.filter(is_cheaper=True).count(),
                        'expensive_products': shop_analyses.filter(is_cheaper=False, price_difference__gt=0).count(),
                        'equal_price_products': shop_analyses.filter(price_difference=0).count(),
                        'total_price_difference': shop_analyses.aggregate(total_diff=Sum('price_difference'))['total_diff'] or 0,
                        'avg_price_difference': shop_analyses.aggregate(avg_diff=Avg('price_difference'))['avg_diff'] or 0,
                        'analyses': serialized_data
                    }
            
            if not response_data:
                return Response(
                    {'message': 'Seçilen mağazalar için karşılaştırma sonucu bulunamadı'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': 'Karşılaştırma sonuçları getirilirken bir hata oluştu: ' + str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
