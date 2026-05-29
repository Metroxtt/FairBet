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

    def test_estados_evento_completos(self):
        self.assertIn(Event.Estado.SCHEDULED, Event.Estado)
        self.assertIn(Event.Estado.LIVE, Event.Estado)
        self.assertIn(Event.Estado.SUSPENDED, Event.Estado)
        self.assertIn(Event.Estado.FINISHED, Event.Estado)
        self.assertIn(Event.Estado.CANCELLED, Event.Estado)

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

    def test_filtro_por_estado(self):
        Event.objects.create(equipo_local='A', equipo_visitante='B', fecha_hora='2026-07-01 15:00:00', estado=Event.Estado.SCHEDULED)
        Event.objects.create(equipo_local='C', equipo_visitante='D', fecha_hora='2026-07-02 15:00:00', estado=Event.Estado.LIVE)
        qs = Event.objects.filter(estado=Event.Estado.LIVE)
        self.assertEqual(qs.count(), 1)

    def test_busqueda_por_equipo(self):
        Event.objects.create(equipo_local='Perú', equipo_visitante='Brasil', fecha_hora='2026-07-01 15:00:00')
        Event.objects.create(equipo_local='Argentina', equipo_visitante='Uruguay', fecha_hora='2026-07-02 15:00:00')
        qs = Event.objects.filter(equipo_local__icontains='Perú')
        self.assertEqual(qs.count(), 1)

    def test_ordering_por_fecha(self):
        e1 = Event.objects.create(equipo_local='A', equipo_visitante='B', fecha_hora='2026-07-10 15:00:00')
        e2 = Event.objects.create(equipo_local='C', equipo_visitante='D', fecha_hora='2026-07-05 15:00:00')
        qs = Event.objects.all()
        self.assertEqual(qs.first(), e2)

    def test_mercados_anidados_en_evento(self):
        event = Event.objects.create(equipo_local='Perú', equipo_visitante='Brasil', fecha_hora='2026-07-01 15:00:00')
        Market.objects.create(event=event, tipo=Market.Tipo.ONE_X_TWO, cuota_local=Decimal('2.0'), cuota_empate=Decimal('3.0'), cuota_visitante=Decimal('4.0'))
        self.assertEqual(event.markets.count(), 1)

    def test_estados_market(self):
        self.assertIn(Market.Estado.OPEN, Market.Estado)
        self.assertIn(Market.Estado.SUSPENDED, Market.Estado)
        self.assertIn(Market.Estado.SETTLED, Market.Estado)

    def test_margen_default(self):
        event = Event.objects.create(equipo_local='X', equipo_visitante='Y', fecha_hora='2026-07-01 15:00:00')
        market = Market.objects.create(event=event, tipo=Market.Tipo.ONE_X_TWO, cuota_local=Decimal('2.0'), cuota_empate=Decimal('3.0'), cuota_visitante=Decimal('4.0'))
        self.assertEqual(market.margen, Decimal('0.05'))
