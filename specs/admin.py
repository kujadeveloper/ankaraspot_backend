from django.contrib import admin
from .models import SpecsModel, SpecValueModel

# Register your models here.
class SpecsAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

class SpecValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('value',)

admin.site.register(SpecsModel, SpecsAdmin)
admin.site.register(SpecValueModel, SpecValueAdmin)