"""
Tests para la app events (Leonardo).
Basado en: Sesión 03 (ORM), Sesión 05 (DRF testing)
"""
from django.test import TestCase
from .models import Event, Market
from decimal import Decimal


class EventModelTest(TestCase):
    def test_crear_evento(self):
        event = Event.objects.create(
            equipo_local='Perú',
            equipo_visitante='Brasil',
            fecha_hora='2026-06-14 15:00:00'
        )
        self.assertEqual(str(event), 'Perú vs Brasil')
        self.assertEqual(event.estado, Event.Estado.SCHEDULED)

    def test_crear_market(self):
        event = Event.objects.create(
            equipo_local='Perú', equipo_visitante='Brasil',
            fecha_hora='2026-06-14 15:00:00'
        )
        market = Market.objects.create(
            event=event, tipo=Market.Tipo.ONE_X_TWO,
            cuota_local=Decimal('3.50'), cuota_empate=Decimal('3.20'),
            cuota_visitante=Decimal('2.10'), margen=Decimal('0.05')
        )
        self.assertEqual(market.event, event)
