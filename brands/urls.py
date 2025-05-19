from django.urls import path

from brands.views import BrandView

urlpatterns = [
    path('', BrandView.as_view({'get': 'list'}), name='brands'),
]
