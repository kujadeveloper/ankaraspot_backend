import json
import os

from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from attachment.models import AttachmentModel
from mail.models import MailModel
from shops.models import ShopModel
from shops.serializers import ShopSerializer

from .serializers import UserSerializer, SshKeySerializer, SubScribeSerializer, UserMeSerializer,ChangePasswordSerializer,NotificationSerializer
from .models import User, SshKeyModel, NotificationModel
from .shema import shema

from utils.utils import generate_unique_id, generate_random_string, generate_custom_random_key, custom_hash

from google.oauth2 import id_token
from google.auth.transport.requests import Request
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _



class UsersPublicView(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    @swagger_auto_schema(request_body=shema['UsersView']['create'],
                         operation_description=shema['UsersView']['create_descriptions'])
    def create(self, request):
        user_type = request.data.get('type', None)

        request.data['username'] = request.data['email']
        if request.data['password'] != request.data['repassword']:
            raise ValidationError('Şifreniz eşleşmiyor.')

        request.data['confirm_code'] = generate_random_string()
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if user_type == 'company':
            user.groups.add(3)
            print(request.data['web_url'])
            shop = ShopModel.objects.create(name=request.data['company'],
                                            web_url=request.data['web_url'])
            user.shop = shop
            user.save()
        else:
            user.groups.add(2)

        custom_key = generate_custom_random_key(20, use_punctuation=True)
        token = custom_hash(custom_key)
        if user is not None:
            user.confirm_token = token
            user.save()

            content = json.dumps({'url': os.getenv('FRONTEND_URI') + '/auth-page/confirm_mail/' + token,
                                  'name': f'{user.first_name} {user.last_name}'})
            MailModel.objects.create(user=user, mail_type=0, to=user.email,
                                     subject='FİYATOR HESABINIZI ONAYLAYIN', content=content)

        return Response({'success': True, 'message': 'Kayıt oluşturuldu.', 'data': serializer.data})

    @swagger_auto_schema(request_body=shema['UsersPublicView']['subscribe'],
                         operation_description='')
    def subscriber(self, request):
        serializer = SubScribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'message': 'Kayıt oluşturuldu.', 'data': serializer.data})

    @swagger_auto_schema(request_body=shema['UsersPublicView']['forgot_pass'])
    def forgot_pass(self, request):
        email = request.data['email']
        user = User.objects.filter(email=email, is_deleted=False, is_active=True).first()

        custom_key = generate_custom_random_key(20, use_punctuation=True)
        token = custom_hash(custom_key)

        if user is not None:
            user.confirm_token = token
            user.save()

            content = json.dumps({'url': os.getenv('FRONTEND_URI') + '/auth-page/reset-password/' + token,
                                  'name': f'{user.first_name} {user.last_name}'})
            MailModel.objects.create(user=user, mail_type=1, to=user.email,
                                     subject='FİYATOR ŞİFREMİ UNUTTUM', content=content)

        return Response({'success': True, 'message': 'OK.'})

    @swagger_auto_schema(request_body=shema['UsersPublicView']['reset_pass'])
    def reset_pass(self, request):
        password = request.data['password']
        repassword = request.data['repassword']
        token = request.data['token']
        user = User.objects.filter(is_deleted=False, is_active=True, confirm_token=token).first()

        if user is not None:
            serializer = UserSerializer(user, data={'password': password, 'confirm_token': ''}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response({'success': True, 'message': 'OK.'})

    @swagger_auto_schema(request_body=shema['UsersPublicView']['confirm_key'])
    def confirm_key(self, request):
        confirm_key = request.data.get('confirm_key', None)
        if confirm_key is None:
            return Response({'success': False, 'message': 'Error.'})
        users = User.objects.filter(confirm_token=confirm_key, is_deleted=False, is_active=False).first()
        if users:
            users.is_active = True
            users.save()
            return Response({'success': True, 'message': 'OK.'})
        else:
            return Response({'success': False, 'message': 'Error.'})


class UsersView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @swagger_auto_schema(request_body=shema['UsersView']['update'],
                         operation_description=shema['UsersView']['update_descriptions'])
    def update(self, request):
        id_ = request.user.id
        instance = User.objects.filter(id=id_, is_deleted=False).first()

        if 'company' in request.data:

            if instance.shop is None:
                request.data['name'] = request.data['company']
                serialzier = ShopSerializer(data=request.data)
                serialzier.is_valid(raise_exception=True)
                shop = serialzier.save()
                instance.shop = shop
                instance.tax_number = request.data['tax_number']
                instance.save()
            else:
                instance.shop.name = request.data['company']
                instance.shop.url = request.data['url']
                instance.shop.trendyol_api_key = request.data['trendyol_api_key']
                instance.shop.trendyol_api_secret = request.data['trendyol_api_secret']
                instance.shop.trendyol_shop_id = request.data['trendyol_shop_id']
                instance.shop.cargo_barem = request.data['cargo_barem']
                instance.shop.web_url = request.data['web_url']
                instance.shop.shop_title = request.data['shop_title']
                instance.tax_number = request.data['tax_number']
                instance.save()
                if 'images' in request.data:
                    instance.shop.images = AttachmentModel.objects.get(pk=request.data['images'])
                if 'tax_document' in request.data:
                    if request.data['tax_document'] is not None:
                        instance.shop.tax_document = AttachmentModel.objects.get(pk=request.data['tax_document'])
                instance.shop.save()
        else:
            serializer = UserMeSerializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response({'success': True, 'message': 'Kayıt oluşturuldu.'})

    @swagger_auto_schema(request_body=shema['UsersView']['delete'],
                         operation_description=shema['UsersView']['delete_descriptions'])
    def delete(self, request):
        id_ = request.data.get('id', None)
        item = User.objects.get(pk=id_)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(manual_parameters=shema['UsersView']['lists'],
                         operation_description=shema['UsersView']['list_descriptions'])
    def lists(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        if id_ is not None:
            response = User.objects.filter(is_deleted=False, id=id_).first()
            serializer = UserSerializer(response)
            return Response({'success': True, 'data': serializer.data})
        else:
            response = User.objects.filter(is_deleted=False).all()

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        serializers = UserSerializer(result_page, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(operation_description=shema['UsersView']['create_anonym_descriptions'])
    def create_anonym(self, request):
        try:
            session = request.session['anonymous_user_id']
        except:
            unique_id = generate_unique_id()
            request.session['anonymous_user_id'] = unique_id
            anonymous_user_id = request.session['anonymous_user_id']
            User.objects.create(anonym=anonymous_user_id, username='anonym_' + anonymous_user_id,
                                email=anonymous_user_id + '@anonym.com')
        return Response({'success': True, 'user': request.session['anonymous_user_id']})

    @swagger_auto_schema(manual_parameters=shema['UsersView']['lists'],
                         operation_description=shema['UsersView']['list_descriptions'])
    def lists_ssh_key(self, request):
        page_size = request.GET.get('page_size', 10)
        id_ = request.GET.get('id', None)
        if id_ is not None:
            response = SshKeyModel.objects.filter(is_deleted=False, id=id_).first()
            serializer = SshKeySerializer(response)
            return Response({'success': True, 'data': serializer.data})
        else:
            response = SshKeyModel.objects.filter(is_deleted=False, user=request.user.id).all()

        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(response, request)
        serializers = SshKeySerializer(result_page, many=True)
        data = paginator.get_paginated_response(serializers.data).data
        return Response({'success': True, 'data': data})

    @swagger_auto_schema(operation_description=shema['UsersView']['create_anonym_descriptions'])
    def create_ssh_key(self, request):
        request.data['user'] = request.user.id
        serializer = SshKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True})

    @swagger_auto_schema(operation_description=shema['UsersView']['create_anonym_descriptions'])
    def delete_ssh_key(self, request):
        id_ = request.data['id']
        key = SshKeyModel.objects.filter(is_deleted=False, id=id_).first()

        if key is not None:
            key.is_deleted = True
            key.save()

        return Response({'success': True})

    def me(self, request):
        if request.user is not None:
            response = User.objects.filter(is_deleted=False, id=request.user.id).first()

            serializer = UserMeSerializer(response)
            data = serializer.data

            return Response({'success': True, 'data': data})
        return Response({'success': False}, status.HTTP_400_BAD_REQUEST)

    def get_token(self, user):
        if user.is_deleted:
            raise ValidationError({'detail': 'Not found'})
        token = super().get_token(user)
        token['success'] = True
        # Add custom claims if needed
        # token['custom_claim'] = 'custom_value'
        return token

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def get_token(self, user):
        if user.is_deleted:
            raise ValidationError({'detail': 'Not found'})
        token = super().get_token(user)
        token['success'] = True
        # Add custom claims if needed
        # token['custom_claim'] = 'custom_value'
        return token
    
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Google OAuth2 login endpoint",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'token': openapi.Schema(type=openapi.TYPE_STRING, description='Google OAuth2 ID token')
            },
            required=['token']
        ),
        responses={
            200: "Login successful - Returns JWT tokens",
            201: "New user created and logged in - Returns JWT tokens", 
            400: "Invalid token"
        }
    )
    def post(self, request):
        # Google'dan gelen token'ı al
        token = request.data.get('token')

        try:
            # Google token'ını doğrula
            idinfo = id_token.verify_oauth2_token(
                token, 
                Request(), 
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=10
            )

            # Token'ın Google tarafından verildiğini kontrol et
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')

            # Kullanıcı bilgilerini al
            email = idinfo['email']
            if not idinfo.get('email_verified', False):
                raise ValueError('Email not verified by Google.')
                
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Kullanıcı modelini al
            User = get_user_model()
            user = User.objects.filter(email=email).first()

            # Eğer kullanıcı zaten varsa, giriş yap
            if user:
                if not user.is_active:
                    user.is_active = True
                    user.save()
                    
                refresh = RefreshToken.for_user(user)
                return Response({
                    "success": True,
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": user.email
                }, status=status.HTTP_200_OK)

            # Yeni kullanıcı oluştur
            user = User.objects.create_user(
                email=email,
                username=email,
                password=None,
                first_name=first_name,
                last_name=last_name,
                is_active=True
            )
            user.groups.add(2)  # Varsayılan kullanıcı grubuna ekle
            
            # Yeni kullanıcı için token oluştur
            refresh = RefreshToken.for_user(user)
            return Response({
                "success": True,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": user.email
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Kullanıcı şifresini değiştirme",
        request_body=ChangePasswordSerializer
    )
    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if not user.check_password(serializer.validated_data['current_password']):
            return Response({"error": "Mevcut şifre yanlış."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(serializer.validated_data['new_password'], user=user)
        except ValidationError as e:
            error_messages = [
                # {"error": _("Yeni şifre yeterince uzun değil.")} if 'too short' in message else
                # {"error": _("Yeni şifre güvenli değil.")} if 'too common' in message else
                # {"error": _("Yeni şifre sadece rakamlardan oluşamaz.")} if 'entirely numeric' in message else
                # {"error": _("Yeni şifre kullanıcı adıyla çok benzer.")} if 'similar to the username' in message else
                # {"error": _("Yeni şifre e-posta adresiyle çok benzer.")} if 'similar to the email' in message else
                # {"error": _("Yeni şifre adınızla çok benzer.")} if 'similar to the first name' in message else
                # {"error": _("Yeni şifre soyadınızla çok benzer.")} if 'similar to the last name' in message else
                {"error": _("Yeni şifre en az bir karakter içermelidir.")} if 'must contain at least one character' in message else
                {"error": _("Yeni şifre en az 8 karakter uzunluğunda olmalıdır.")} if 'must be at least 8 characters long' in message else
                {"error": _(message)}
                for message in e.messages
            ]
            return Response({"error": [{"success": False, "errors": error_messages}]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({"success": "Şifre başarıyla güncellendi."}, status=status.HTTP_200_OK)


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Bildirimleri al",
        manual_parameters=[
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Sayfa boyutu",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: "Bildirimler başarıyla alındı",
            400: "Geçersiz istek"
        }
    )
    def get(self, request):
        # Sayfa boyutunu al, varsayılan 10
        page_size = int(request.GET.get('page_size', 10))
        
        # Tüm bildirimleri tek sorguda al
        notifications = NotificationModel.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        # Okunmuş ve okunmamış bildirimleri ayır
        unread_notifications = [n for n in notifications if not n.status]
        read_notifications = [n for n in notifications if n.status]

        # Sayfalama için paginator oluştur
        paginator = PageNumberPagination()
        paginator.page_size = page_size

        # Bildirimleri sayfala
        unread_page = paginator.paginate_queryset(unread_notifications, request) or []
        read_page = paginator.paginate_queryset(read_notifications, request) or []

        # Her iki grubu da serialize et
        unread_serializer = NotificationSerializer(unread_page, many=True)
        read_serializer = NotificationSerializer(read_page, many=True)
        
        # Yanıtı hazırla ve gönder
        return Response({
            'success': True,
            'data': {
                'unread': unread_serializer.data,
                'read': read_serializer.data
            },
            'count': {
                'unread': len(unread_notifications),
                'read': len(read_notifications)
            }
        })

    @swagger_auto_schema(
        operation_description="Bildirimleri okundu olarak işaretle",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Bildirim ID'),
                'status': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Bildirim durumu')
            },
            required=['id', 'status']
        ),
        responses={
            200: "Bildirimler başarıyla okundu olarak işaretlendi",
            404: "Bildirim bulunamadı"
        }
    )
    def post(self, request):
        notification = NotificationModel.objects.filter(
            id=request.data.get('id'),
            user=request.user
        ).first()

        if not notification:
            return Response({"success": False, "message": "Bildirim bulunamadı"}, status=404)

        notification.status = request.data.get('status', True)
        notification.save()
        
        serializer = NotificationSerializer(notification)
        return Response({"success": True, "data": serializer.data})