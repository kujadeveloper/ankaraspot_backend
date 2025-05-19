from django.db import models
from users.models import User
from django.conf import settings
import os
import uuid


# Create your models here.
class AttachmentModel(models.Model):
    class Meta:
        verbose_name_plural = "Resimler"
        ordering = ['id']
        db_table = 'attachment'

    def __str__(self):
        if self.id and self.name:
            return f'[{self.id}] {self.name}'
        elif self.name:
            return f'Yeni Resim - {self.name}'
        elif self.id:
            return f'Resim {self.id}'
        return 'Yeni Resim'  # Fallback string

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='users_attachment')
    name = models.CharField(max_length=500)
    original_file_url = models.CharField(max_length=500, blank=True, null=True, db_index=True)
    thumb_file_url = models.CharField(max_length=500)
    original_name = models.CharField(max_length=500, blank=True, null=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FileMetadataModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'file_meta_data'

    file_name = models.CharField(max_length=500)
    file_url = models.URLField(max_length=500)
    file_hash = models.CharField(max_length=150)
    file_size_byte = models.IntegerField(default=0)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)