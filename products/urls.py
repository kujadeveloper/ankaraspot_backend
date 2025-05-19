from django.urls import path

from categories.views import CategoriesView
from products.views import ProductsView, ProductAuthView, ProductPriceUpdateView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

urlpatterns = [
    path('', ProductsView.as_view({'get': 'list'}), name='products'),
]
