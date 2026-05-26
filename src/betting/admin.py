from django.contrib import admin
from .models import Bet, ComboBet, ComboLeg


class ComboLegInline(admin.TabularInline):
    model = ComboLeg
    extra = 1


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'seleccion', 'monto', 'cuota_al_apostar', 'estado', 'created_at']
    list_filter = ['estado']
    search_fields = ['user__email', 'user__dni']


@admin.register(ComboBet)
class ComboBetAdmin(admin.ModelAdmin):
    list_display = ['user', 'monto', 'cuota_total', 'estado', 'created_at']
    list_filter = ['estado']
    inlines = [ComboLegInline]
