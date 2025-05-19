from django.urls import path
from specs.views import SpecsView
from django.urls import path


urlpatterns = [
    path('', SpecsView.as_view({'get': 'get_spect_value'}), name='spects'),
    path('create/', SpecsView.as_view({'post': 'create_spec'}), name='create-spec'),
]
