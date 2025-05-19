from django.db import models

from attachment.models import AttachmentModel


class BrandModel(models.Model):
    class Meta:
        verbose_name_plural = "Marka Listesi"  # Plural name
        ordering = ['id']
        db_table = 'brands'

    def __str__(self):
        return f"{self.name} ({self.id})"

    name = models.CharField(max_length=200)
    is_main = models.BooleanField(default=False, null=False, blank=False)
    is_popular = models.BooleanField(default=False, null=False, blank=False)
    image = models.ForeignKey(AttachmentModel,
                              blank=True,
                              null=True,
                              related_name="brand_image",
                              on_delete=models.SET_NULL)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


