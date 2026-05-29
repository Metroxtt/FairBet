from django.test import TestCase
from decimal import Decimal
from .models import Account, LedgerEntry, transfer, check_deposit_limit
from users.models import User, DepositLimit
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase


class WalletTransferTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', dni='12345678',
            nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='test123'
        )
        self.from_acct = Account.objects.create(account_type=Account.Tipo.CASA)
        LedgerEntry.objects.create(account=self.from_acct, credit=Decimal('1000'), description='Saldo Inicial Casa')

        self.to_acct = Account.objects.create(user=self.user, account_type=Account.Tipo.WALLET_USUARIO)

    def test_transferencia_exitosa(self):
        transfer(self.from_acct, self.to_acct, Decimal('100'), 'Test transfer')
        self.assertEqual(self.from_acct.balance, Decimal('900'))
        self.assertEqual(self.to_acct.balance, Decimal('100'))

    def test_saldo_insuficiente(self):
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.to_acct, Decimal('9999'), 'Sin saldo')

    def test_idempotencia(self):
        from uuid import uuid4
        key = uuid4()
        transfer(self.from_acct, self.to_acct, Decimal('50'), 'Primera', idempotency_key=key)
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.to_acct, Decimal('50'), 'Duplicada', idempotency_key=key)

    def test_monto_cero(self):
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.to_acct, Decimal('0'), 'Monto cero')

    def test_monto_negativo(self):
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.to_acct, Decimal('-50'), 'Monto negativo' )

    def test_idempotencia_monto_distinto(self):
        from uuid import uuid4
        key = uuid4()
        transfer(self.from_acct, self.to_acct, Decimal('50'), 'Original', idempotency_key=key)
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.to_acct, Decimal('100'), 'Distinto monto', idempotency_key=key)

    def test_transferencia_self_account(self):
        with self.assertRaises(ValueError):
            transfer(self.from_acct, self.from_acct, Decimal('100'), 'self transfer')


class HypothesisWalletTest(HypothesisTestCase):
    def setUp(self):
        User.objects.filter(email='hypo@test.com').delete()
        self.user = User.objects.create_user(
            email='hypo@test.com', dni='12345678',
            nombre='Hipothesis', apellido='test',
            fecha_nacimiento='2000-01-01', password='test123'
        )

    @given(
        monto = st.decimals(min_value='0.01', max_value='10000',
                            allow_nan=False, allow_infinity=False, places=4)
    )
    @settings(max_examples=50)
    def test_invarianza_partida_doble(self,monto):
        from_acct = Account.objects.create(account_type=Account.Tipo.CASA)
        LedgerEntry.objects.create(account=from_acct, credit=Decimal('1000000'), description='Init')
        to_acct = Account.objects.create(user=self.user, account_type=Account.Tipo.WALLET_USUARIO)

        transfer(from_acct, to_acct, monto, 'TEST HYPOTHESIS')

        # Para verificar la partida doble de la transferencia, validamos solo los registros de la transferencia
        # (excluyendo el registro de inicialización manual que rompe la partida doble)
        transfer_entries = LedgerEntry.objects.filter(description='TEST HYPOTHESIS')
        total_debits = sum(transfer_entries.values_list('debit', flat=True))
        total_credits = sum(transfer_entries.values_list('credit', flat=True))
        self.assertEqual(total_debits, total_credits)

    @given(
        monto = st.decimals(min_value='0.01', max_value='10000',
                            allow_nan=False, allow_infinity=False, places=4)
    )
    @settings(max_examples=50)
    def test_saldo_nunca_negativo(self,monto):
        from_acct = Account.objects.create(account_type=Account.Tipo.CASA)
        LedgerEntry.objects.create(account=from_acct, credit=Decimal('5000'), description='Init')
        to_acct = Account.objects.create(user=self.user, account_type=Account.Tipo.WALLET_USUARIO)
        
        assume(monto <= from_acct.balance)

        transfer(from_acct, to_acct, monto, 'TEST SALDO NEGATIVO')

        self.assertGreaterEqual(from_acct.balance, Decimal('0'))
        self.assertGreaterEqual(to_acct.balance, Decimal('0'))

    def test_generacion_hash_inmutable(self):
        from_acct = Account.objects.create(account_type=Account.Tipo.CASA)
        LedgerEntry.objects.create(account=from_acct, credit=Decimal('1000'), description='Init')
        to_acct = Account.objects.create(user=self.user, account_type=Account.Tipo.WALLET_USUARIO)
        
        transfer(from_acct, to_acct, Decimal('100'), 'Test hash 1')
        transfer(from_acct, to_acct, Decimal('200'), 'Test hash 2')
        
        entries = LedgerEntry.objects.filter(account=to_acct).order_by('created_at', 'id')
        
        for i, entry in enumerate(entries):
            self.assertIsNotNone(entry.hash)
            if i > 0:
                self.assertEqual(entry.previous_hash, entries[i-1].hash)


class DepositLimitTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='limit@test.com', dni='87654321',
            nombre='Limit', apellido='User',
            fecha_nacimiento='2000-01-01', password='test123'
        )
        self.casa_acct = Account.objects.create(account_type=Account.Tipo.CASA)
        LedgerEntry.objects.create(account=self.casa_acct, credit=Decimal('10000'), description='Init casa')
        self.user_acct = Account.objects.create(user=self.user, account_type=Account.Tipo.WALLET_USUARIO)
        
    def test_default_limit_creation(self):
        # No debería lanzar excepción
        check_deposit_limit(self.user, Decimal('500'))
        
    def test_daily_limit_exceeded(self):
        limit = DepositLimit.objects.get(user=self.user)
        limit.daily_limit = Decimal('100')
        limit.monthly_limit = Decimal('500')
        limit.save()
        
        # Simula depósito previo
        transfer(self.casa_acct, self.user_acct, Decimal('80'), 'Depósito inicial')
        
        with self.assertRaisesMessage(ValueError, 'Este depósito excede tu límite diario de 100.00'):
            check_deposit_limit(self.user, Decimal('30'))

    def test_monthly_limit_exceeded(self):
        from django.utils import timezone
        from datetime import timedelta
        
        limit = DepositLimit.objects.get(user=self.user)
        limit.daily_limit = Decimal('500')
        limit.monthly_limit = Decimal('600')
        limit.save()
        
        # Simula depósito viejo de hace 2 días
        transfer(self.casa_acct, self.user_acct, Decimal('400'), 'Depósito viejo')
        
        old_time = timezone.now() - timedelta(days=2)
        LedgerEntry.objects.filter(account=self.user_acct).update(created_at=old_time)
        
        with self.assertRaisesMessage(ValueError, 'Este depósito excede tu límite mensual de 600.00'):
            # Nuevo depósito de 300: 
            # Diario: 300 <= 500 (ok)
            # Mensual: 400 + 300 = 700 > 600 (falla)
            check_deposit_limit(self.user, Decimal('300'))
