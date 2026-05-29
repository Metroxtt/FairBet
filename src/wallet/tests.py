
from django.test import TestCase
from decimal import Decimal
from .models import Account, LedgerEntry, transfer
from users.models import User
from hypothesis import given, strategies as st, assume, settings
from hypothesis.extra.django import TestCase as HypothesisTestCase


class WalletTransferTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', dni='12345678',
            nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='test123'
        )
        self.from_acct = Account.objects.create(
            account_type=Account.Tipo.CASA, balance=Decimal('1000')
        )
        self.to_acct = Account.objects.create(
            user=self.user, account_type=Account.Tipo.WALLET_USUARIO
        )

    def test_transferencia_exitosa(self):
        transfer(self.from_acct, self.to_acct, Decimal('100'), 'Test transfer')
        self.from_acct.refresh_from_db()
        self.to_acct.refresh_from_db()
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
        from_acct = Account.objects.create(
            account_type = Account.Tipo.CASA, balance = Decimal('1000000')
        )
        to_acct = Account.objects.create(
            user= self.user, account_type=Account.Tipo.WALLET_USUARIO
        )

        transfer(from_acct,to_acct,monto, 'TEST HYPOTHESIS')

        total_debits = sum(LedgerEntry.objects.values_list('debit',flat=True))
        total_credits = sum(LedgerEntry.objects.values_list('credit',flat=True))
        self.assertEqual(total_debits, total_credits)

    @given(
        monto = st.decimals(min_value='0.01', max_value='10000',
                            allow_nan=False, allow_infinity=False, places=4)

    )
    @settings(max_examples=50)
    def test_saldo_nunca_negativo(self,monto):
        from_acct = Account.objects.create(
            account_type = Account.Tipo.CASA, balance = Decimal('5000')
        )
        to_acct = Account.objects.create(
            user = self.user, account_type=Account.Tipo.WALLET_USUARIO

        )
        assume(monto <= from_acct.balance)

        transfer(from_acct, to_acct, monto,'TEST SALDO NEGATIVO')
        from_acct.refresh_from_db()
        to_acct.refresh_from_db()

        self.assertGreaterEqual(from_acct.balance, Decimal('0'))
        self.assertGreaterEqual(to_acct.balance, Decimal('0'))

    @given(
        monto=st.decimals(min_value='0.01',max_value='10000',allow_nan=False,allow_infinity=False,places=4)
    )
    @settings(max_examples=50)
    def test_balance_after_correcto(self,monto):
        from_acct = Account.objects.create(
            account_type= Account.Tipo.CASA, balance = Decimal('1000000')
        )
        to_acct = Account.objects.create(
            user = self.user , account_type = Account.Tipo.WALLET_USUARIO
        )
        transfer(from_acct, to_acct, monto,'TEST BALANCE AFTER')

        entries = LedgerEntry.objects.filter(account= to_acct)
        for entry in entries:
            esperado = Decimal('0') + entry.credit - entry.debit
            self.assertEqual(entry.balance_after,esperado)
        
    
