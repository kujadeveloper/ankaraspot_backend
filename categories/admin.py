from django.contrib import admin
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

# Register your models here.
from .models import CategoriesModel


class CategoryFilter(admin.SimpleListFilter):
    title = 'parent_cat'
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        return CategoriesModel.CATEGORIES_LIST

    def queryset(self, request, queryset):
        if self.value() == 'main_cat':
            return queryset.filter(parent=None, shop=None)
        return queryset


class CategoryAdminForm(forms.ModelForm):
    description = forms.CharField(
        widget=CKEditor5Widget(),
        required=False,
        label='Açıklama'
    )

    class Meta:
        model = CategoriesModel
        fields = '__all__'


class CategoryAdmin(admin.ModelAdmin):
    form = CategoryAdminForm
    list_display = ('id', 'name', 'parent', 'shop', 'order')
    search_fields = ('id', 'name')
    list_per_page = 20
    list_filter = (CategoryFilter,)
    raw_id_fields = ('parent', 'images', 'shop', 'match', 'brands', 'specs')
    list_select_related = ('parent', 'shop', 'match', 'images')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'brands', 'specs'
        ).select_related(*self.list_select_related)


admin.site.register(CategoriesModel, CategoryAdmin)
