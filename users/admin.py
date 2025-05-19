from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .models import NotificationModel

# Register your models here.
class UserAdmin(UserAdmin):
    model = User
    list_display = ['id', 'email', 'username', 'is_active', 'is_staff', 'shop']
    list_filter = ['id', 'email', 'username', 'is_active', 'is_staff', 'shop']
    fieldsets = (
        (None, {'fields': ('email', 'password','first_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'shop')}),
        # ... Diğer özelleştirmeleri burada ekleyebilirsiniz ...
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'shop')}
        ),
    )
    search_fields = ['email']
    ordering = ['email']

admin.site.register(User, UserAdmin)



@admin.register(NotificationModel)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'subject', 'title', 'status']
    list_filter = ['status']
    search_fields = ['subject', 'title']
    ordering = ['-created_at']
    fieldsets = (
        (None, {
            'fields': ('user', 'subject', 'title', 'content', 'status')
        }),
    )
