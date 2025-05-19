from django.db import models
from attachment.models import AttachmentModel
from brands.models import BrandModel
from users.models import User


class SubMerchantModel(models.Model):
    class Meta:
        ordering = ['-id']
        db_table = 'sub_merchant_shop'

    shop = models.ForeignKey('shops.ShopModel', on_delete=models.CASCADE)
    name = models.CharField(max_length=400)
    images = models.ForeignKey(AttachmentModel, on_delete=models.CASCADE, blank=True, null=True,
                               related_name='attachment_sub_merchant_shop')
    merchant = models.IntegerField(blank=True, null=True)
    url = models.CharField(max_length=500, blank=True, null=True)

    sync_service = models.IntegerField(default=0, blank=True, null=True)

    score = models.IntegerField(default=0, blank=True, null=True)

    shop_description = models.CharField(max_length=500, blank=True, null=True)
    brands = models.ManyToManyField(BrandModel, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ShopCommentModel(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=False)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ShopModel(models.Model):
    class Meta:
        ordering = ['-id']
        db_table = 'shop'
        verbose_name_plural = "Mağaza Listesi"  # Plural name
    def __str__(self):
        return f"{self.name} ({self.id})"

    name = models.CharField(max_length=400)
    shop_title = models.CharField(max_length=200, blank=True, null=True)
    web_url = models.CharField(max_length=500, blank=True, null=True)
    images = models.ForeignKey(AttachmentModel, on_delete=models.CASCADE, blank=True, null=True,
                               related_name='attachment_shop')
    tax_document = models.ForeignKey(AttachmentModel, on_delete=models.CASCADE, blank=True, null=True,
                                     related_name='tax_document_shop')
    comment = models.ManyToManyField(ShopCommentModel, blank=True, related_name="shop_comment")
    sub_merchant = models.ManyToManyField(SubMerchantModel, blank=True, related_name='sub_merchant_shop')
    url = models.CharField(max_length=500, blank=True, null=True)
    is_browser = models.BooleanField(default=False)
    cargo_barem = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      default=0.0,
                                      blank=True,
                                      null=True)
    xml_map = models.ManyToManyField('XMlMapsModel', blank=True, related_name='xml_map_shop')
    html_map = models.ManyToManyField('HtmlFieldModel', blank=True, related_name='html_map_shop')

    trendyol_api_key = models.CharField(max_length=100, blank=True, null=True)
    trendyol_api_secret = models.CharField(max_length=100, blank=True, null=True)
    trendyol_shop_id = models.CharField(max_length=100, blank=True, null=True)

    ikas_api_key = models.CharField(max_length=2000, blank=True, null=True)
    ikas_image_bucket = models.CharField(max_length=500, blank=True, null=True)
    shop_description = models.CharField(max_length=500, blank=True)
    brands = models.ManyToManyField(BrandModel, blank=True)

    #0 xml
    #1 csv
    sync_service = models.IntegerField(default=0, blank=True, null=True)

    is_active_sync = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_is_active = self.is_active

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._original_is_active = self.is_active

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.save()

    def undelete(self, *args, **kwargs):
        self.is_deleted = False
        self.save()


class XMlMapsModel(models.Model):
    class Meta:
        ordering = ['-id']
        db_table = 'shop_xml_maps'
        verbose_name_plural = "Eşleştirme Alanları"  # Plural name

    def __str__(self):
        return f"{self.field_name} ({self.value})"

    field_name = models.CharField(max_length=400)
    value = models.CharField(max_length=400)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class HtmlFieldModel(models.Model):
    class Meta:
        ordering = ['-id']
        db_table = 'shop_html_maps'
        verbose_name_plural = "HTML Eşleştirme Alanları"  # Plural name

    tag = models.CharField(max_length=200, blank=True, null=True)
    tag_class = models.CharField(max_length=400, blank=True, null=True)
    tag_id = models.CharField(max_length=400, blank=True, null=True)
    tag_attr = models.CharField(max_length=1000, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=400)
    priority = models.IntegerField(default=0, blank=True, null=True)
    order = models.IntegerField(default=0, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)