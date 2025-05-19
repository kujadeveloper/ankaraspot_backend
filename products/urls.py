from django.urls import path

from categories.views import CategoriesView
from products.views import ProductsView, ProductAuthView, ProductPriceUpdateView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

urlpatterns = [
    path('', ProductsView.as_view({'get': 'list'}), name='products'),
    path('search', ProductsView.as_view({'get': 'search'}), name='search_products'),
    path('before-search', ProductsView.as_view({'get': 'search_first_info'}), name='before-search'),
    path('main-page', ProductsView.as_view({'get': 'main_page'}), name='main-page'),
    path('discounted', ProductsView.as_view({'get': 'discounted'}), name='discounted_products'),
    path('favorite', ProductsView.as_view({'get': 'get_favorite', 'post': 'favorite'}), name='favorite_products'),
    path('price-alarm', ProductsView.as_view({'get': 'get_price_alarm', 'post': 'price_alarm'}),
         name='price_alarm_products'),
    path('categories', ProductsView.as_view({'get': 'categories_products'}),
         name='categories_products'),
    path('events', ProductsView.as_view({'get': 'product_click'}), name='product_events'),
    path('events-list', ProductAuthView.as_view({'get': 'product_event_list'}), name='product_event_list'),
    path('comments', ProductAuthView.as_view({'get': 'get_comments'}), name='product_get_comments'),
    path('comment', ProductAuthView.as_view({
        'post': 'post_comment',
        'put': 'put_comment',
        'delete': 'delete_comment'
    }), name='product_comment'),
    path('rate', ProductAuthView.as_view({'post': 'rate'}), name='product_rate'),
    path('my_products', ProductAuthView.as_view({'get': 'product_list'}), name='my_products'),
    path('get-url-product', ProductsView.as_view({'get': 'get_url_product'}), name='get_url_product'),
    path('populer-product', ProductsView.as_view({'get': 'populer_products'}), name='populer-product'),
    path('hightlight-product', ProductsView.as_view({'get': 'highlight_products'}), name='hightlight-product'),
    path('youtube-video', ProductAuthView.as_view({'get': 'youtube_video'}), name='youtube-video'),
    path('general-info', ProductsView.as_view({'get': 'general_info'}), name='general_info'),
    path('search-scroll/', ProductsView.as_view({'get': 'search_with_scroll'}), name='product-search-scroll'),
    path('update-price/', ProductPriceUpdateView.as_view(), name='update-price'),
    path('price-history/', ProductsView.as_view({'get':'get_price_history'}), name='get-price-history'),
]
