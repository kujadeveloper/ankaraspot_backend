from django.db import models
from attachment.models import AttachmentModel
from shops.models import ShopModel
from django.utils.text import slugify

import re
import unicodedata
from brands.models import BrandModel
from specs.models import SpecsModel


# Create your models here.

class CategoriesModel(models.Model):
    CATEGORIES_LIST = [
        ('main_cat', 'Main Kategoriler'),
        ('all', 'Tüm kategoriler'),
    ]

    class Meta:
        verbose_name_plural = "Kategoriler"
        ordering = ['created_at']
        db_table = 'categories'

    parent = models.ForeignKey("CategoriesModel", blank=True, null=True, on_delete=models.SET_NULL,
                               related_name='children')
    images = models.ForeignKey(AttachmentModel, on_delete=models.CASCADE, blank=True, null=True,
                               related_name='attachment_category')
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, blank=True, null=True,
                             related_name='shop_category')
    match = models.ForeignKey("CategoriesModel", blank=True, null=True, on_delete=models.SET_NULL,
                              related_name='match_category')
    brands = models.ManyToManyField(BrandModel, blank=True, related_name="categories_brand")

    specs = models.ManyToManyField(SpecsModel, blank=True, related_name="categories_specs")
    name = models.CharField(max_length=1000, db_index=True)
    order = models.IntegerField(default=0)
    slug = models.SlugField(max_length=1000)
    commission = models.DecimalField(null=True, blank=True, decimal_places=2, max_digits=10)
    product_count = models.IntegerField(default=0,null=True, blank=True)
    is_show_main = models.BooleanField(default=False, null=True, blank=True)
    is_status = models.BooleanField(default=True, null=True, blank=True)
    is_adult = models.BooleanField(default=False, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = models.TextField(verbose_name='Açıklama', blank=True, null=True)

    def get_children(self):
        data = self.children.filter(is_deleted=False)
        return data

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        self.is_deleted = False
        self.save()

    def save(self, *args, **kwargs):
        turkish_map = str.maketrans({
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
        })
        text = self.name.translate(turkish_map)
        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s-]+', '-', text).strip('-')
        self.slug = slugify(text)
        super().save(*args, **kwargs)

    def get_breadcrumb(self):
        breadcrumb = []
        category = self
        while category:
            breadcrumb.append({'name': category.name, 'id': category.id, 'slug': category.slug})
            category = category.parent
        return list(reversed(breadcrumb))

    @property
    def bread_crumb(self):
        return self.get_breadcrumb()
