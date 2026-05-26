from django.contrib import admin
from .models import User, DepositLimit


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['dni', 'email', 'nombre', 'apellido', 'edad', 'is_active', 'is_excluded']
    list_filter = ['is_active', 'is_excluded', 'is_staff']
    search_fields = ['dni', 'email', 'nombre', 'apellido']


@admin.register(DepositLimit)
class DepositLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_limit', 'weekly_limit', 'monthly_limit']
