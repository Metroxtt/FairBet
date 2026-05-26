import uuid
from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from wallet.models import Account, transfer


class Bet(models.Model):
    class Estado(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        WON = 'won', 'Ganada'
        LOST = 'lost', 'Perdida'
        CANCELLED = 'cancelled', 'Cancelada'
        CASHED_OUT = 'cashed_out', 'Retirada'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bets')
    event = models.ForeignKey('events.Event', on_delete=models.PROTECT, related_name='bets')
    market = models.ForeignKey('events.Market', on_delete=models.PROTECT, related_name='bets')
    seleccion = models.CharField('selección', max_length=20)
    cuota_al_apostar = models.DecimalField('cuota', max_digits=10, decimal_places=4)
    monto = models.DecimalField('monto', max_digits=18, decimal_places=4)
    estado = models.CharField('estado', max_length=20, choices=Estado.choices, default=Estado.PENDING)
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('creado el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado el', auto_now=True)

    class Meta:
        verbose_name = 'apuesta'
        verbose_name_plural = 'apuestas'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} - {self.event} - ${self.monto}'

    @property
    def pago_potencial(self):
        return self.monto * self.cuota_al_apostar

    def settle(self, resultado_evento):
        if self.estado != self.Estado.PENDING:
            raise ValueError(f'La apuesta ya está en estado {self.estado}')

        ganadora = self.seleccion == resultado_evento

        with transaction.atomic():
            user_account = Account.objects.select_for_update().get(
                user=self.user, account_type=Account.Tipo.WALLET_USUARIO
            )
            casa_account = Account.objects.select_for_update().get(
                account_type=Account.Tipo.CASA
            )
            pendientes_account = Account.objects.select_for_update().get(
                account_type=Account.Tipo.APUESTAS_PENDIENTES
            )

            if ganadora:
                ganancia = self.monto * self.cuota_al_apostar
                transfer(pendientes_account, user_account, ganancia,
                         f'Pago apuesta {self.pk}')
                self.estado = self.Estado.WON
            else:
                transfer(pendientes_account, casa_account, self.monto,
                         f'Apuesta perdida {self.pk}')
                self.estado = self.Estado.LOST

            self.save(update_fields=['estado'])


class ComboBet(models.Model):
    class Estado(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        WON = 'won', 'Ganada'
        LOST = 'lost', 'Perdida'
        CANCELLED = 'cancelled', 'Cancelada'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='combo_bets')
    monto = models.DecimalField('monto', max_digits=18, decimal_places=4)
    cuota_total = models.DecimalField('cuota total', max_digits=10, decimal_places=4)
    estado = models.CharField('estado', max_length=20, choices=Estado.choices, default=Estado.PENDING)
    idempotency_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('creado el', auto_now_add=True)

    class Meta:
        verbose_name = 'apuesta combinada'
        verbose_name_plural = 'apuestas combinadas'

    def __str__(self):
        return f'Combo {self.user} - ${self.monto}'


class ComboLeg(models.Model):
    combo = models.ForeignKey(ComboBet, on_delete=models.CASCADE, related_name='legs')
    event = models.ForeignKey('events.Event', on_delete=models.PROTECT)
    market = models.ForeignKey('events.Market', on_delete=models.PROTECT)
    seleccion = models.CharField('selección', max_length=20)
    cuota = models.DecimalField('cuota', max_digits=10, decimal_places=4)

    class Meta:
        verbose_name = 'pierna de combo'
        verbose_name_plural = 'piernas de combo'
