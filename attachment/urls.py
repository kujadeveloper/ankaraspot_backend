from django.urls import path
from .views import AttachmentView

urlpatterns = [
    path('', AttachmentView.as_view({'get': 'list', 'post': 'create'}), name='attachement'),
]
