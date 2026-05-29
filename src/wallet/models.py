import hashlib
import uuid
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta


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

    @property
    def balance(self):
        totals = self.entries.aggregate(
            total_credit=Sum('credit', default=Decimal('0')),
            total_debit=Sum('debit', default=Decimal('0'))
        )
        return totals['total_credit'] - totals['total_debit']


class LedgerEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='entries')
    debit = models.DecimalField('débito', max_digits=18, decimal_places=4, default=Decimal('0'))
    credit = models.DecimalField('crédito', max_digits=18, decimal_places=4, default=Decimal('0'))
    description = models.CharField('descripción', max_length=255)
    previous_hash = models.CharField('hash anterior', max_length=64, null=True, blank=True)
    hash = models.CharField('hash', max_length=64, unique=True, null=True, blank=True)
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'asiento contable'
        verbose_name_plural = 'asientos contables'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.id} - {self.account} - ${self.credit - self.debit}'

    def generate_hash(self):
        prev = self.previous_hash or ('0' * 64)
        data = f"{prev}{self.id}{self.account_id}{self.debit}{self.credit}{self.description}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def save(self, *args, **kwargs):
        if not self.hash:
            last_entry = LedgerEntry.objects.filter(account=self.account).order_by('-created_at', '-id').first()
            if last_entry:
                self.previous_hash = last_entry.hash
            else:
                self.previous_hash = '0' * 64
            
            self.hash = self.generate_hash()
            
        super().save(*args, **kwargs)


def transfer(from_account, to_account, amount, description, idempotency_key=None):
    if idempotency_key and LedgerEntry.objects.filter(id=idempotency_key).exists():
        raise ValueError(f'Operación duplicada: {idempotency_key}')

    amount = Decimal(str(amount))
    if amount <= 0:
        raise ValueError('El monto debe ser positivo')

    if from_account.pk == to_account.pk:
        raise ValueError('No puedes transferir a la misma cuenta')

    account_ids = sorted([from_account.pk, to_account.pk])

    with transaction.atomic():
        accounts = Account.objects.select_for_update().filter(pk__in=account_ids)
        accounts_dict = {acc.pk: acc for acc in accounts}
        
        from_acct = accounts_dict[from_account.pk]
        to_acct = accounts_dict[to_account.pk]

        if from_acct.balance < amount:
            raise ValueError('Saldo insuficiente')

        entry_id = idempotency_key or uuid.uuid4()
        
        from_acct.version += 1
        from_acct.save(update_fields=['version'])

        to_acct.version += 1
        to_acct.save(update_fields=['version'])

        LedgerEntry.objects.create(
            id=entry_id,
            account=from_acct,
            debit=amount,
            credit=Decimal('0'),
            description=description,
        )
        LedgerEntry.objects.create(
            account=to_acct,
            debit=Decimal('0'),
            credit=amount,
            description=description,
        )


def check_deposit_limit(user, amount):
    limit = getattr(user, 'deposit_limit', None)
    if not limit:
        from users.models import DepositLimit
        limit, _ = DepositLimit.objects.get_or_create(user=user)
    
    amount = Decimal(str(amount))
    now = timezone.now()
    
    start_of_day = now - timedelta(days=1)
    start_of_month = now - timedelta(days=30)
    
    account = getattr(user, 'wallet_account', None)
    if not account:
        return

    daily_deposits = LedgerEntry.objects.filter(
        account=account,
        credit__gt=0,
        description__icontains='depósito',
        created_at__gte=start_of_day
    ).aggregate(total=Sum('credit'))['total'] or Decimal('0')

    monthly_deposits = LedgerEntry.objects.filter(
        account=account,
        credit__gt=0,
        description__icontains='depósito',
        created_at__gte=start_of_month
    ).aggregate(total=Sum('credit'))['total'] or Decimal('0')

    if daily_deposits + amount > limit.daily_limit:
        raise ValueError(f'Este depósito excede tu límite diario de ${limit.daily_limit}')
    
    if monthly_deposits + amount > limit.monthly_limit:
        raise ValueError(f'Este depósito excede tu límite mensual de ${limit.monthly_limit}')
