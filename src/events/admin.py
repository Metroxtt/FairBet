from django.contrib import admin
from .models import Event, Market


class MarketInline(admin.TabularInline):
    model = Market
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['equipo_local', 'equipo_visitante', 'fecha_hora', 'estado', 'resultado']
    list_filter = ['estado']
    search_fields = ['equipo_local', 'equipo_visitante']
    inlines = [MarketInline]


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ['event', 'tipo', 'cuota_local', 'cuota_empate', 'cuota_visitante', 'estado']
    list_filter = ['tipo', 'estado']
