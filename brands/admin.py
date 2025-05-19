from django.contrib import admin
from django import forms
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

from .models import BrandModel
from categories.models import CategoriesModel

class BrandAdminForm(forms.ModelForm):
    is_popular = forms.BooleanField(label='Popüler Marka', required=False)
    
    class Meta:
        model = BrandModel
        fields = '__all__'

class CategoryFilter(admin.SimpleListFilter):
    title = _('Kategoriler')
    parameter_name = 'category'

    def lookups(self, request, model_admin):
        categories = (CategoriesModel.objects
                    .filter(is_deleted=False)
                    .annotate(brand_count=Count('brands'))
                    .filter(brand_count__gt=0)
                    .only('id', 'name')
                    .order_by('-brand_count'))
        
        return [(category.id, f"{category.name} ({category.brand_count})") for category in categories]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(categories_brand__id=self.value())
        return queryset

class Admin(admin.ModelAdmin):
    form = BrandAdminForm
    list_display = ('id', 'name', 'is_popular', 'category_list','is_deleted')
    search_fields = ('name',)
    list_per_page = 20
    list_select_related = ()
    list_filter = ('is_popular', CategoryFilter)
    list_editable = ('is_popular',)
    
    def category_list(self, obj):
        try:
            categories = list(obj.categories_brand.values_list('name', flat=True)[:3])
            return ', '.join(categories) + ('...' if len(categories) > 3 else '')
        except Exception:
            return ''
    category_list.short_description = _('Kategoriler')

    def get_queryset(self, request):
        return (super().get_queryset(request)
               .prefetch_related('categories_brand')
               .only('id', 'name', 'is_popular'))

admin.site.register(BrandModel, Admin)