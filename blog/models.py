from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django_ckeditor_5.fields import CKEditor5Field
from attachment.models import AttachmentModel

# Create your models here.

class BlogModel(models.Model):
    title = models.CharField(max_length=255, db_index=True,null=True, blank=True)
    content = CKEditor5Field(blank=True, null=True, config_name='default')
    image = models.ForeignKey(AttachmentModel, on_delete=models.CASCADE, null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.BooleanField(default=True, verbose_name='Aktif/Pasif')

    def save(self, *args, **kwargs):
        # Slug alanı boşsa, title'dan otomatik olarak oluştur.
        if not self.slug:
            self.slug = slugify(self.title)
        super(BlogModel, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']