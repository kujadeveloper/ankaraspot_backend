from django.urls import path

from for_developer.views import ForDeveloperView

urlpatterns = [
    path('', ForDeveloperView.as_view({'get': 'get'}), name='for_developer'),
]
