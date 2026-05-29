from django.test import TestCase
from decimal import Decimal
from .models import Bet
from events.models import Event, Market
from users.models import User
from wallet.models import Account


class BetStateMachineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', dni='12345678',
            nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='test123'
        )
        self.event = Event.objects.create(
            equipo_local='Peru', equipo_visitante='Brasil',
            fecha_hora='2026-06-14 15:00:00'
        )
        self.market = Market.objects.create(
            event=self.event, tipo=Market.Tipo.ONE_X_TWO,
            cuota_local=Decimal('3.50'), cuota_empate=Decimal('3.20'),
            cuota_visitante=Decimal('2.10')
        )
        Account.objects.get_or_create(
            user=self.user, account_type=Account.Tipo.WALLET_USUARIO
        )
        Account.objects.get_or_create(
            account_type=Account.Tipo.CASA, defaults={'balance': 1000000}
        )
        Account.objects.get_or_create(
            account_type=Account.Tipo.APUESTAS_PENDIENTES
        )

    def test_bet_pending_on_create(self):
        bet = Bet.objects.create(
            user=self.user, event=self.event, market=self.market,
            seleccion='local', cuota_al_apostar=Decimal('3.50'),
            monto=Decimal('100')
        )
        self.assertEqual(bet.estado, Bet.Estado.PENDING)
        self.assertEqual(bet.pago_potencial, Decimal('350'))

    def test_settle_won_changes_state(self):
        bet = Bet.objects.create(
            user=self.user, event=self.event, market=self.market,
            seleccion='local', cuota_al_apostar=Decimal('2.0'),
            monto=Decimal('100')
        )
        bet.settle('local')
        bet.refresh_from_db()
        self.assertEqual(bet.estado, Bet.Estado.WON)

    def test_settle_lost_changes_state(self):
        bet = Bet.objects.create(
            user=self.user, event=self.event, market=self.market,
            seleccion='local', cuota_al_apostar=Decimal('2.0'),
            monto=Decimal('100')
        )
        bet.settle('visita')
        bet.refresh_from_db()
        self.assertEqual(bet.estado, Bet.Estado.LOST)

    def test_settle_already_settled_raises_error(self):
        bet = Bet.objects.create(
            user=self.user, event=self.event, market=self.market,
            seleccion='local', cuota_al_apostar=Decimal('2.0'),
            monto=Decimal('100')
        )
        bet.settle('local')
        with self.assertRaises(ValueError):
            bet.settle('local')

    def test_pago_potencial_calculation(self):
        bet = Bet.objects.create(
            user=self.user, event=self.event, market=self.market,
            seleccion='empate', cuota_al_apostar=Decimal('3.20'),
            monto=Decimal('200')
        )
        self.assertEqual(bet.pago_potencial, Decimal('640'))
