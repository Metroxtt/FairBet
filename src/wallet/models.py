import uuid
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings


class Account(models.Model):
    class Tipo(models.TextChoices):
        WALLET_USUARIO = 'wallet_usuario', 'Billetera de Usuario'
        CASA = 'casa', 'Cuenta de la Casa'
        APUESTAS_PENDIENTES = 'apuestas_pendientes', 'Apuestas Pendientes'
        BONOS = 'bonos', 'Bonos Promocionales'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wallet_account', null=True, blank=True
    )
    account_type = models.CharField('tipo', max_length=30, choices=Tipo.choices)
    balance = models.DecimalField('saldo', max_digits=18, decimal_places=4, default=Decimal('0'))
    version = models.IntegerField('versión', default=1)
    created_at = models.DateTimeField('creado el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado el', auto_now=True)

    class Meta:
        verbose_name = 'cuenta'
        verbose_name_plural = 'cuentas'

    def __str__(self):
        if self.user:
            return f'{self.get_account_type_display()} - {self.user}'
        return f'{self.get_account_type_display()} (sistema)'


class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='entries')
    debit = models.DecimalField('débito', max_digits=18, decimal_places=4, default=Decimal('0'))
    credit = models.DecimalField('crédito', max_digits=18, decimal_places=4, default=Decimal('0'))
    balance_after = models.DecimalField('saldo después', max_digits=18, decimal_places=4)
    description = models.CharField('descripción', max_length=255)
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'asiento contable'
        verbose_name_plural = 'asientos contables'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.id} - {self.account} - ${self.credit - self.debit}'


def transfer(from_account, to_account, amount, description, idempotency_key=None):
    if idempotency_key and LedgerEntry.objects.filter(id=idempotency_key).exists():
        raise ValueError(f'Operación duplicada: {idempotency_key}')

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError('El monto debe ser positivo')

    with transaction.atomic():
        from_acct = Account.objects.select_for_update().get(pk=from_account.pk)
        to_acct = Account.objects.select_for_update().get(pk=to_account.pk)

        if from_acct.balance < amount:
            raise ValueError('Saldo insuficiente')

        entry_id = idempotency_key or uuid.uuid4()
        from_acct.balance -= amount
        from_acct.version += 1
        from_acct.save(update_fields=['balance', 'version'])

        to_acct.balance += amount
        to_acct.version += 1
        to_acct.save(update_fields=['balance', 'version'])

        LedgerEntry.objects.create(
            id=entry_id,
            account=from_acct,
            debit=amount,
            credit=Decimal('0'),
            balance_after=from_acct.balance,
            description=description,
        )
        LedgerEntry.objects.create(
            account=to_acct,
            debit=Decimal('0'),
            credit=amount,
            balance_after=to_acct.balance,
            description=description,
        )
