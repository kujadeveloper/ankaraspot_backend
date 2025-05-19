from django.contrib import admin
from tasks.models import TasksModel


# Register your models here.

class Admin(admin.ModelAdmin):
    list_display = ('id', 'name', 'page', 'status', 'created_at', 'updated_at', 'is_deleted')
    list_per_page = 20

admin.site.register(TasksModel, Admin)
