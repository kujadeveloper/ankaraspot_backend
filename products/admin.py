from django.contrib import admin
from django import forms
from django.http import JsonResponse
from django.urls import path, reverse

from .models import ProductModel, ProductSearchHistoryModel
from specs.models import SpecsModel, SpecValueModel  # Import both models

class ProductAdminForm(forms.ModelForm):
    spec_values = forms.ModelMultipleChoiceField(
        queryset=SpecValueModel.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'select2',
            'style': 'width: 100%; min-height: 150px;'
        })
    )

    class Meta:
        model = ProductModel
        fields = ('id', 'name', 'category','brand', 'price', 'is_deleted', 'stock')

    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['spec_values'].queryset = SpecValueModel.objects.all()

class ProductModelAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('id', 'name', 'image', 'shop', 'brand', 'link', 'is_deleted')
    search_fields = ('id', 'name')
    list_per_page = 20
    change_form_template = 'admin/products/productmodel/change_form.html'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('shop', 'brand', 'image').prefetch_related('gallery', 'match', 'price_history')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.specs = SpecsModel.objects.all()
        return form

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['specs'] = SpecsModel.objects.all()
        extra_context['available_specs'] = SpecsModel.objects.all()
        return super().change_view(request, object_id, form_url, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('spec-values/<int:spec_id>/',
                 self.admin_site.admin_view(self.get_spec_values),
                 name='productmodel_get_spec_values'),
        ]
        return custom_urls + urls

    def get_spec_values(self, request, spec_id):
        try:
            spec = SpecsModel.objects.get(id=spec_id)
            values = SpecValueModel.objects.filter(specs_id=spec_id).values('id', 'value')
            return JsonResponse({'values': list(values)})
        except SpecsModel.DoesNotExist:
            return JsonResponse({'error': 'Spec not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

@admin.register(ProductSearchHistoryModel)
class ProductSearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'search_term', 'search_type', 'created_at')
    search_fields = ('search_term', 'user__username')
    list_filter = ('search_type', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

admin.site.register(ProductModel, ProductModelAdmin)
