from django.urls import path
from .views import BalanceViewSet, TransactionViewSet,PaymentCallbackView

urlpatterns = [
    # Bakiye detaylarını görüntüleme endpoint'i
    path('balance/', BalanceViewSet.as_view({'get': 'retrieve'}), name='balance-detail'),
    # Para yatırma endpoint'i
    path('deposit/', BalanceViewSet.as_view({'post': 'deposit'}), name='balance-deposit'),
    # Harcama yapma endpoint'i
    path('spend/', BalanceViewSet.as_view({'post': 'spend'}), name='balance-spend'),
    # İşlem geçmişini listeleme endpoint'i
    path('transactions/', TransactionViewSet.as_view({'get': 'list'}), name='transaction-list'),
    # Ödeme başarılı callback endpoint'i
    path('payment/success/', PaymentCallbackView.as_view(), name='payment_success'),
    # Ödeme hatalı callback endpoint'i
    path('payment/error/', PaymentCallbackView.as_view(), name='payment_error'),
]