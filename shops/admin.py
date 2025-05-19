from django.contrib import admin

from attachment.models import AttachmentModel
from brands.models import BrandModel

# Register your models here.
from .models import ShopModel, XMlMapsModel
from django import forms
from django.utils.html import mark_safe
from django_select2.forms import Select2Widget


class AdminModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        data = args[0] if args else None
        image = None
        if data and isinstance(data, dict):
            image = data.get('images')
            print(image)
        if image is None:
            if self.instance.images is None:
                image = None
            else:
                image = self.instance.images.id
        if self.instance.images is None:
            self.fields['images'].queryset = AttachmentModel.objects.filter(is_deleted=False, id=image).all()
        else:
            if image is None:
                self.fields['images'].queryset = AttachmentModel.objects.filter(is_deleted=False).all()[:1]
            else:
                self.fields['images'].queryset = AttachmentModel.objects.filter(is_deleted=False, id=image).all()
    class Meta:
        model = XMlMapsModel
        fields = '__all__'
        widgets = {
            'xml_map': admin.widgets.FilteredSelectMultiple('XML Maps', is_stacked=False),
            'brands': admin.widgets.FilteredSelectMultiple('Markalar', is_stacked=False),
            'images': Select2Widget(
                attrs={'data-ajax--url': '/attachment/'}
            )
        }


class Admin(admin.ModelAdmin):
    form = AdminModelForm
    list_display = ('id', 'name', 'url', 'images_url', 'xml_map_display', 'sync_service', 'is_active_sync', 'shop_title', 'is_active', 'is_browser')
    search_fields = ('id', 'name') 
    list_per_page = 20
    list_editable = ('is_active',)

    def images_url(self, obj):
        image = obj.images.id if obj.images else None
        if image is None:
            return None
        else:
            return mark_safe(f'<img src="{obj.images.thumb_file_url}" height="50" />')

    images_url.short_description = 'Images'

    fieldsets = (
        (None, {
            'fields': ('name', 'url', 'images', 'shop_title', 'is_active')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('xml_map', 'sync_service', 'ikas_api_key','ikas_image_bucket', 'trendyol_api_key',
                       'cargo_barem','trendyol_api_secret', 'trendyol_shop_id',
                       'is_deleted', 'is_active_sync', 'shop_description', 'brands','is_browser'),
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'images':
            # Get the last 50 AttachmentModel records
            kwargs['queryset'] = AttachmentModel.objects.all()[:1]

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def xml_map_display(self, obj):
        return ", ".join([str(xml_map.value) for xml_map in obj.xml_map.all()])

    xml_map_display.short_description = 'XML Maps'


class XMLMapsAdmin(admin.ModelAdmin):
    model = XMlMapsModel
    list_display = ('id', 'field_name', 'value')


admin.site.register(ShopModel, Admin)
admin.site.register(XMlMapsModel, XMLMapsAdmin)