from django.urls import path
from .views import BlogListAPIView, BlogDetailAPIView

urlpatterns = [
    path('blogs/', BlogListAPIView.as_view(), name='blog_list'),
    path('blog_detail/<slug:slug>/', BlogDetailAPIView.as_view(), name='blog_detail'),
]
