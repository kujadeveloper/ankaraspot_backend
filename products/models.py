from django.db import models
from django.db.models import Count, Q, Case, When, F, Value, IntegerField
from django.db.models.signals import pre_save
from django.dispatch import receiver

from brands.models import BrandModel
from categories.models import CategoriesModel
from shops.models import ShopModel, SubMerchantModel
from specs.models import SpecsModel, SpecValueModel
from users.models import User
from attachment.models import AttachmentModel


class ProductPriceModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'products_prices'

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, blank=True, null=True,
                             related_name='product_price_shop')
    sub_merchant_shop = models.ForeignKey(SubMerchantModel, on_delete=models.CASCADE, blank=True, null=True,
                                          related_name='product_price_sub_merchant_shop')

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)


class ProductRateModel(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    rate = models.IntegerField(default=1, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductCommentModel(models.Model):
    class Meta:
        ordering = ['id']
        
    product = models.ForeignKey('ProductModel', on_delete=models.CASCADE, related_name='product_comments',blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=False)
    rating = models.IntegerField(default=0, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductModel(models.Model):
    class Meta:
        verbose_name_plural = "Ürün Listesi"  # Plural name
        ordering = ['id']
        db_table = 'products'

    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             blank=True,
                             null=True,
                             related_name='product_user')

    category = models.ForeignKey(CategoriesModel, on_delete=models.CASCADE, blank=True, null=True,
                                 related_name='product_category')

    shop = models.ForeignKey(ShopModel, on_delete=models.CASCADE, blank=True, null=True, related_name='product_shop')

    sub_merchant_shop = models.ForeignKey(SubMerchantModel, on_delete=models.CASCADE,
                                          blank=True,
                                          null=True,
                                          related_name='product_sub_merchant_shop')

    command_count = models.IntegerField(default=0, blank=True, null=True)

    image = models.ForeignKey(AttachmentModel,
                              blank=True,
                              null=True,
                              related_name="product_image",
                              on_delete=models.SET_NULL)
    brand = models.ForeignKey(BrandModel,
                              on_delete=models.CASCADE,
                              blank=True,
                              null=True,
                              related_name='product_brand')

    gallery = models.ManyToManyField(AttachmentModel,
                                     blank=True,
                                     related_name="product_gallery")

    match = models.ManyToManyField('ProductModel',
                                   blank=True,
                                   related_name="product_match")

    name = models.CharField(max_length=1000, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(max_length=2000)
    slug = models.SlugField(max_length=1000)

    model_code = models.CharField(max_length=255, blank=True, null=True)
    barcode = models.CharField(max_length=255, blank=True, null=True, db_index=True)

    stock = models.IntegerField(default=0, blank=True, null=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    specs = models.ManyToManyField('specs.SpecsModel', blank=True, related_name='product_specs')
    spec_values = models.ManyToManyField(SpecValueModel, blank=True, related_name='product_spec_values')
    video_url = models.CharField(max_length=1000, blank=True, null=True)

    gtin_13 = models.CharField(max_length=255, blank=True, null=True)

    cargo_price = models.DecimalField(max_digits=10,
                                      decimal_places=2,
                                      blank=True,
                                      null=True)

    price = models.DecimalField(max_digits=10,
                                decimal_places=2,
                                default=0.0,
                                blank=True,
                                null=True)

    price_history = models.ManyToManyField(ProductPriceModel, blank=True, related_name="product_product_history")
    rate = models.ManyToManyField(ProductRateModel, blank=True, related_name="product_rate")
    comment = models.ManyToManyField(ProductCommentModel, blank=True, related_name="product_comment")

    kdv = models.FloatField(default=20, blank=True, null=True)

    dimensionalWeight = models.FloatField(default=0.0,
                                          blank=True,
                                          null=True)
    syncronize_status = models.BooleanField(default=False)
    is_match = models.BooleanField(default=False)
    status = models.IntegerField(default=0,
                                 blank=True,
                                 null=True)
    host_name = models.CharField(max_length=255, blank=True, null=True)
    #update_function = models.CharField(max_length=255, blank=True, null=True)
    #is_lock = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    # Skor alanları
    total_match_count = models.IntegerField(default=0, blank=True, null=True)
    total_shop_count = models.IntegerField(default=0, blank=True, null=True)
    match_score = models.IntegerField(default=1, blank=True, null=True)  # Default 1 çünkü hiç eşleşme yoksa 1 puan
    shop_score = models.IntegerField(default=0, blank=True, null=True)
    final_score = models.IntegerField(default=1, blank=True, null=True)  # Default 1 çünkü match_score default 1


class ProductUserClickModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'products_user_clicks'
        verbose_name_plural = "Kullanıcı Tıklamaları"  # Plural name

    ip = models.GenericIPAddressField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    browser = models.CharField(max_length=1000, blank=True, null=True)
    browser_version = models.CharField(max_length=1000, blank=True, null=True)
    os_family = models.CharField(max_length=255, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    device = models.CharField(max_length=255, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductEventModel(models.Model):
    class Meta:
        verbose_name_plural = "Ürün Tıklamaları"  # Plural name
        ordering = ['id']
        db_table = 'products_events'


    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='event_product')
    click = models.ManyToManyField(ProductUserClickModel, blank=True, related_name='event_click')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductDiscountModel(models.Model):
    class Meta:
        ordering = ['id']
        db_table = 'products_discount'

    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='discount_product')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductFavoriteModel(models.Model):
    class Meta:
        ordering = ['id']

    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='favorite_product')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_user')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductPriceAlarmModel(models.Model):
    class Meta:
        ordering = ['id']

    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='price_alarm_product')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alarm_user')
    price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductListUserView(models.Model):
    class Meta:
        ordering = ['id']

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listview_user')
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='listview_product')

    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ProductSearchHistoryModel(models.Model):
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Arama Geçmişi"
        db_table = 'products_search_history'

    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='search_history_user')
    search_term = models.CharField(max_length=1000, blank=True, null=True)
    search_type = models.CharField(max_length=50, blank=True, null=True, help_text="search veya search_first_info")
    
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
