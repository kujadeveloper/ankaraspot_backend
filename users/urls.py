from django.urls import path
from .views import GoogleLoginView, UsersView, UsersPublicView,ChangePasswordView,NotificationView

urlpatterns = [
    path('', UsersView.as_view({'delete': 'delete', 'put': 'update'}), name='users'),
    path('registry', UsersPublicView.as_view({'post': 'create'}), name='users_create'),
    path('me', UsersView.as_view({'get': 'me'}), name='me'),
    path('confirm-key', UsersPublicView.as_view({'post': 'confirm_key'}), name='confirm_key'),
    path('forgot-password', UsersPublicView.as_view({'post': 'forgot_pass'}), name='forgot_pass'),
    path('reset-password', UsersPublicView.as_view({'post': 'reset_pass'}), name='reset_pass'),
    path('subscriber', UsersPublicView.as_view({'post': 'subscriber'}), name='users_subscriber'),
    path('google-login', GoogleLoginView.as_view(), name='google-login'),
    path('change-password', ChangePasswordView.as_view(), name='change_password'),
    path('notification', NotificationView.as_view(), name='notification'),
]
