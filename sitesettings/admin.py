from django.contrib import admin

from sitesettings.models import SitesettingsModels


# Register your models here.
class Admin(admin.ModelAdmin):
    list_display = (
        'id', 'cdn_systems', 'mail_systems', 'aws_access_key', 'aws_secret', 'aws_url', 'bucket', 'is_deleted')
    list_per_page = 20


admin.site.register(SitesettingsModels, Admin)
