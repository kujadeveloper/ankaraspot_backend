from django.urls import path

from categories.views import CategoriesView, CategoriesAuthView

urlpatterns = [
    path('', CategoriesView.as_view({'get': 'list'}), name='categories'),
    path('spects', CategoriesView.as_view({'get': 'spec_list'}), name='spects'),
    path('category-filter', CategoriesView.as_view({'get': 'category_filters'}), name='category_filters'),
    path('my-categories', CategoriesAuthView.as_view({'get': 'list', 'put': 'update_match'}), name='my_category'),
    path('all-categories', CategoriesView.as_view({'get': 'get_all_child'}), name='all-categories'),
    path('all-json-categories', CategoriesView.as_view({'get': 'categories_json'}), name='all-json-categories'),
    path('category-detail', CategoriesView.as_view({'get': 'category_info'}), name='category-detail'),
]
