from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from decimal import Decimal
from .models import Balance, Transaction
from .serializers import BalanceSerializer, TransactionSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.conf import settings
from zeep import Client
from zeep.exceptions import TransportError, XMLSyntaxError, Fault
import hashlib
import base64
import requests.exceptions


# SHA256 hash'ini base64 ile kodlanmış şekilde hesaplar
def calculate_sha2b64(client_code, guid, taksit, islem_tutar, toplam_tutar, siparis_id, hata_url, basarili_url):
    hash_string = f"{client_code}{guid}{taksit}{islem_tutar}{toplam_tutar}{siparis_id}{hata_url}{basarili_url}"
    sha256_hash = hashlib.sha256(hash_string.encode('utf-8')).digest()
    return base64.b64encode(sha256_hash).decode('utf-8')


class BalanceViewSet(viewsets.ViewSet):
    # Sadece giriş yapmış kullanıcılar erişebilir
    permission_classes = [IsAuthenticated]

    # Kullanıcının bakiyesini getirir
    def retrieve(self, request):
        balance, _ = Balance.objects.get_or_create(user=request.user)
        serializer = BalanceSerializer(balance)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Yatırılacak miktar'),
                'card_holder': openapi.Schema(type=openapi.TYPE_STRING, description='Kart sahibi'),
                'card_number': openapi.Schema(type=openapi.TYPE_STRING, description='Kart numarası'),
                'expiry_month': openapi.Schema(type=openapi.TYPE_STRING, description='Son kullanma ayı (MM)'),
                'expiry_year': openapi.Schema(type=openapi.TYPE_STRING, description='Son kullanma yılı (YYYY)'),
                'cvc': openapi.Schema(type=openapi.TYPE_STRING, description='CVC kodu'),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description='GSM numarası (5xxxxxxxxx)'),
            },
            required=['amount', 'card_holder', 'card_number', 'expiry_month', 'expiry_year', 'cvc', 'phone']
        ),
        responses={200: openapi.Response('3D URL', openapi.Schema(type=openapi.TYPE_OBJECT, properties={'ucd_url': openapi.Schema(type=openapi.TYPE_STRING)})), 400: 'Bad Request', 502: 'Payment Gateway Error'},
        operation_description="ParamPOS ile gerçek 3D ödeme başlatma"
    )
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        # Kullanıcının bakiyesini al veya oluştur
        balance, _ = Balance.objects.get_or_create(user=request.user)

        # Gerekli alanların kontrolü
        required_fields = ['amount', 'card_holder', 'card_number', 'expiry_month', 'expiry_year', 'cvc', 'phone']
        if not all(request.data.get(field) for field in required_fields):
            return Response({'error': 'Tüm alanlar zorunludur'}, status=status.HTTP_400_BAD_REQUEST)

        # Miktar kontrolü
        try:
            amount = Decimal(request.data['amount'])
            if amount <= 0:
                raise ValueError("Miktar pozitif olmalıdır")
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Sipariş ve ödeme bilgilerini hazırla
        siparis_id = f"ORDER-{balance.id}-{int(amount * 100)}-{request.user.id}"
        hata_url, basarili_url = request.build_absolute_uri('/payment/error/'), request.build_absolute_uri('/payment/success/')
        islem_tutar = toplam_tutar = f"{amount:.2f}"
        ip_addr = request.META.get('REMOTE_ADDR')

        # İşlem hash'ini hesapla
        islem_hash = calculate_sha2b64(settings.PARAM_CLIENT_CODE, settings.PARAM_GUID, "1", islem_tutar, toplam_tutar, siparis_id, hata_url, basarili_url)

        try:
            # ParamPOS API'sine bağlan
            client = Client(f"{settings.PARAM_API_URL}?wsdl")
            response = client.service.Pos_Odeme(
                G={"CLIENT_CODE": settings.PARAM_CLIENT_CODE, "CLIENT_USERNAME": settings.PARAM_CLIENT_USERNAME, "CLIENT_PASSWORD": settings.PARAM_CLIENT_PASSWORD},
                GUID=settings.PARAM_GUID, KK_Sahibi=request.data['card_holder'], KK_No=request.data['card_number'],
                KK_SK_Ay=request.data['expiry_month'], KK_SK_Yil=request.data['expiry_year'], KK_CVC=request.data['cvc'],
                KK_Sahibi_GSM=request.data['phone'], Hata_URL=hata_url, Basarili_URL=basarili_url, Siparis_ID=siparis_id,
                Siparis_Aciklama="Bakiye yükleme", Taksit="1", Islem_Tutar=islem_tutar, Toplam_Tutar=toplam_tutar,
                Islem_Hash=islem_hash, Islem_Guvenlik_Tip="3D", Islem_ID=siparis_id, IPAdr=ip_addr,
                Ref_URL=request.build_absolute_uri('/')
            )
            return Response({'ucd_url': response['UCD_URL']}) if int(response['Sonuc']) > 0 else Response({'error': response['Sonuc_Str']}, status=status.HTTP_400_BAD_REQUEST)
        except (TransportError, requests.exceptions.ConnectionError) as e:
            return Response({'error': 'Bağlantı hatası', 'detail': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except (XMLSyntaxError, Fault, KeyError, AttributeError) as e:
            return Response({'error': 'Ödeme servisi hatası', 'detail': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(type=openapi.TYPE_OBJECT, properties={'amount': openapi.Schema(type=openapi.TYPE_NUMBER, description='Harcanacak miktar')}),
        responses={200: BalanceSerializer, 400: 'Bad Request'},
        operation_description="Bakiyeden para harcama işlemi"
    )
    @action(detail=False, methods=['post'])
    def spend(self, request):
        # Kullanıcının bakiyesini al veya oluştur
        balance, _ = Balance.objects.get_or_create(user=request.user)
        amount = request.data.get('amount', 0)

        try:
            # Harcama miktarı kontrolü
            amount = Decimal(str(amount))
            if amount <= 0:
                return Response({'error': 'Miktar pozitif olmalıdır'}, status=status.HTTP_400_BAD_REQUEST)
            if balance.amount < amount:
                return Response({'error': 'Yetersiz bakiye'}, status=status.HTTP_400_BAD_REQUEST)

            # İşlemi gerçekleştir
            with transaction.atomic():
                balance.amount -= amount
                balance.save()
                Transaction.objects.create(balance=balance, amount=-amount, description="Harcama yapıldı")

            return Response(BalanceSerializer(balance).data)
        except (ValueError, TypeError):
            return Response({'error': 'Geçersiz miktar'}, status=status.HTTP_400_BAD_REQUEST)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    # İşlem geçmişi için sadece okuma izni olan ViewSet
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Sadece kullanıcının kendi işlemlerini göster
        return Transaction.objects.filter(balance__user=self.request.user)


class PaymentCallbackView(APIView):
    # Ödeme sonrası callback işlemleri için view
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Ödeme sonucu parametrelerini al
        sonuc = request.data.get('TURKPOS_RETVAL_Sonuc')
        dekont_id = request.data.get('TURKPOS_RETVAL_Dekont_ID')
        siparis_id = request.data.get('TURKPOS_RETVAL_Siparis_ID')
        tahsilat_tutari = request.data.get('TURKPOS_RETVAL_Tahsilat_Tutari')

        # Gerekli parametrelerin kontrolü
        if not all([sonuc, dekont_id, siparis_id, tahsilat_tutari]):
            return Response({'error': 'Eksik veri'}, status=status.HTTP_400_BAD_REQUEST)

        # Başarılı ödeme durumunda bakiyeyi güncelle
        if int(sonuc) > 0 and int(dekont_id) > 0:
            balance = Balance.objects.get(user=request.user)
            amount = Decimal(tahsilat_tutari.replace(',', '.'))
            with transaction.atomic():
                balance.amount += amount
                balance.save()
                Transaction.objects.create(balance=balance, amount=amount, description=f"ParamPOS ile ödeme (Dekont ID: {dekont_id})")
            return Response({'message': 'Ödeme başarılı'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Ödeme başarısız', 'detail': request.data.get('TURKPOS_RETVAL_Sonuc_Str')}, status=status.HTTP_400_BAD_REQUEST)