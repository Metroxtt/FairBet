"""
Tests para la app wallet (Mark).
Basado en: Sesión 05 (pytest, hypothesis, select_for_update)
"""
from django.test import TestCase
from decimal import Decimal
from .models import Account, LedgerEntry, transfer
from users.models import User


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
