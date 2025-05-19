from django.contrib import admin
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import BlogModel
from django.contrib.admin.widgets import AutocompleteSelect
from django.db import models

class BlogModelAdminForm(forms.ModelForm):
    title = forms.CharField(required=True)
    
    class Meta:
        model = BlogModel
        fields = '__all__'
        widgets = {
            'content': CKEditor5Widget(config_name='default'),
        }

class BlogModelAdmin(admin.ModelAdmin):
    form = BlogModelAdminForm
    list_display = ('title', 'slug', 'created_at', 'updated_at', 'status')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    raw_id_fields = ('image',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "image":
            kwargs["queryset"] = db_field.related_model.objects.filter(is_deleted=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

admin.site.register(BlogModel, BlogModelAdmin)
