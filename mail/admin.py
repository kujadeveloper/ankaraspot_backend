from django.contrib import admin

# Register your models here.
from .models import MailModel


class Admin(admin.ModelAdmin):
    list_display = ('id', 'mail_type', 'to', 'subject', 'status','try_count')
    search_fields = ('id', 'mail_type', 'to')
    list_per_page = 20


admin.site.register(MailModel, Admin)
