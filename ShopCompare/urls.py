from django.urls import path
from .views import ShopComparisonView

urlpatterns = [
    path('compare/', ShopComparisonView.as_view(), name='shop-comparison'),
] 