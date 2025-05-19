from django.contrib import admin
from django.forms.widgets import ClearableFileInput
from django import forms
from utils.s3 import S3, Cloud
# Register your models here.
from .models import AttachmentModel
from .serializers import AttachmentSerializer
import uuid
from django.utils.html import mark_safe


class AdminModelForm(forms.ModelForm):
    image = forms.FileField(
        widget=ClearableFileInput(attrs={
            'class': 'custom-file-input',
            'accept': 'image/*',  # Yalnızca görüntü dosyaları
        }),
        required=False  # Zorunlu değil
    )

    class Meta:
        model = AttachmentModel
        fields = '__all__'
class Admin(admin.ModelAdmin):
    form = AdminModelForm
    list_display = ('id', 'image_th', 'name', 'original_file_url', 'thumb_file_url', 'original_name')
    search_fields = ('id', 'name')
    list_per_page = 20

    def image_th(self, obj):
        image = obj.id if obj.original_file_url else None
        if image is None:
            return None
        else:
            return mark_safe(f'<img src="{obj.original_file_url}" height="50" />')

    def save_model(self, request, obj, form, change):
        # Custom alanı kontrol edelim
        image_file = form.cleaned_data.get('image')

        if image_file:
            s3 = S3()
            orj_filename = str(image_file)
            ext = orj_filename.split('.')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            response_s3 = s3.send_file(image_file, filename, request.user.id)
            obj.original_file_url = response_s3
            obj.thumb_file_url = response_s3

        super().save_model(request, obj, form, change)


admin.site.register(AttachmentModel, Admin)