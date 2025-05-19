from django.urls import path
from .views import *

urlpatterns = [
    path('', MailView.as_view({'get': 'list'}), name='mail'),
]
