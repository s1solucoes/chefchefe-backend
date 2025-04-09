from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin
# Register your models here.


@admin.register(User)
class UserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password', 'phone', 'first_name', 'last_name', 'verified_email', 'verified_phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )