from django.urls import path

from shops.views import ShopViews, ShopAuthViews

urlpatterns = [
    path('', ShopViews.as_view({'get': 'list'}), name='shops'),
    path('comment', ShopAuthViews.as_view({'post': 'comment'}), name='shops_comment'),
    path('comment_list', ShopViews.as_view({'get': 'comment_lists'}), name='comment_list'),
    path('get-url-data', ShopViews.as_view({'get': 'get_url_data'}), name='get_url_data'),
    path('html-map', ShopViews.as_view({'post': 'html_map_create','delete':'html_map_delete'}), name='html_map_create'),
]
