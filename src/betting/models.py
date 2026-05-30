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
                ganancia_neta = ganancia - self.monto
                transfer(casa_account, user_account, ganancia_neta,
                         f'Ganancia apuesta {self.pk}')
                transfer(pendientes_account, user_account, self.monto,
                         f'Devolucion stake apuesta {self.pk}')
                self.estado = self.Estado.WON
            else:
                transfer(pendientes_account, casa_account, self.monto,
                         f'Apuesta perdida {self.pk}')
                self.estado = self.Estado.LOST

            self.save(update_fields=['estado'])

    def cash_out(self):
        if self.estado != self.Estado.PENDING:
            raise ValueError(f'Solo se puede hacer cash-out de apuestas pendientes.')

        if self.event.estado in [Event.Estado.FINISHED, Event.Estado.CANCELLED]:
            raise ValueError(f'No se puede hacer cash-out de un evento {self.event.estado}.')

        # Obtener cuota actual
        cuota_map = {
            'local': self.market.cuota_local,
            'empate': self.market.cuota_empate,
            'visita': self.market.cuota_visitante,
        }
        cuota_actual = cuota_map.get(self.seleccion)
        if not cuota_actual:
            raise ValueError('Selección no válida para el mercado.')

        factor_casa = Decimal('0.90')  # La casa retiene un 10%
        # Formula: cashout = stake * odds_original / odds_actual * factor
        monto_cashout = (self.monto * self.cuota_al_apostar / cuota_actual) * factor_casa
        monto_cashout = round(monto_cashout, 4)

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

            # Liberar el stake de pendientes y enviarlo de vuelta (lo dividiremos lógicamente)
            # Todo el stake de apuestas_pendientes vuelve a la casa (es la forma en que se maneja),
            # o podemos hacerlo más limpio:
            # Transferimos de pendientes a usuario el monto del cashout.
            # Y de pendientes a casa el remanente.
            # Wait, no. Si monto_cashout > stake, la casa tiene que poner la diferencia.
            # Si monto_cashout < stake, la casa se queda con la diferencia.
            
            # Devolvemos todo el stake a la casa desde pendientes
            transfer(pendientes_account, casa_account, self.monto, f'Cashout stake {self.pk}')
            # Pagamos el monto de cashout desde la casa al usuario
            transfer(casa_account, user_account, monto_cashout, f'Pago Cashout {self.pk}')

            self.estado = self.Estado.CASHED_OUT
            self.save(update_fields=['estado'])
        
        return monto_cashout


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

class SuspiciousActivity(models.Model):
    class Severidad(models.TextChoices):
        ALTA = 'alta', 'Alta'
        MEDIA = 'media', 'Media'
        BAJA = 'baja', 'Baja'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alertas_fraude')
    motivo = models.CharField('motivo', max_length=255)
    severidad = models.CharField('severidad', max_length=20, choices=Severidad.choices, default=Severidad.MEDIA)
    fecha = models.DateTimeField('fecha de detección', auto_now_add=True)
    resuelto = models.BooleanField('resuelto', default=False)

    class Meta:
        verbose_name = 'actividad sospechosa'
        verbose_name_plural = 'actividades sospechosas'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.user.dni} - {self.get_severidad_display()} - {self.motivo}'
