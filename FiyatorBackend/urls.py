"""
URL configuration for FiyatorBackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.contrib import admin
from django.urls import path, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path, include, include, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import CustomTokenObtainPairSerializer

schema_view = get_schema_view(
   openapi.Info(
      title="ANKARASPOT API",
      default_version='v1',
      description="Ankaraspot API Documentation",
      terms_of_service="https://www.ankaraspot.com/terms/",
      contact=openapi.Contact(email="info@ankara.com"),
      license=openapi.License(name="Ankaraspot License"),
   ),
   public=True,
   url=os.getenv('BASE_URI'),
)

urlpatterns = [
      path('admin/', admin.site.urls),
      path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
      path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
      path('users/', include('users.urls')),
      path('categories/', include('categories.urls')),
      path('specs/', include('specs.urls')),
      path('products/', include('products.urls')),
      path('brands/', include('brands.urls')),
      path('blog/', include('blog.urls')),
      path('attachment/', include('attachment.urls')),
      path('mail/', include('mail.urls')),
      path('token/', TokenObtainPairView.as_view(serializer_class=CustomTokenObtainPairSerializer), name='token_obtain_pair'),
      path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
      path("ckeditor5/", include('django_ckeditor_5.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
