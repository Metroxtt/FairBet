from django.db import models


class Event(models.Model):
    class Estado(models.TextChoices):
        SCHEDULED = 'scheduled', 'Programado'
        LIVE = 'live', 'En vivo'
        FINISHED = 'finalizado', 'Finalizado'
        CANCELLED = 'cancelado', 'Cancelado'

    class Resultado(models.TextChoices):
        LOCAL = 'local', 'Local'
        EMPATE = 'empate', 'Empate'
        VISITA = 'visita', 'Visita'

    equipo_local = models.CharField('equipo local', max_length=100)
    equipo_visitante = models.CharField('equipo visitante', max_length=100)
    fecha_hora = models.DateTimeField('fecha y hora')
    estado = models.CharField('estado', max_length=20, choices=Estado.choices, default=Estado.SCHEDULED)
    resultado = models.CharField('resultado', max_length=10, choices=Resultado.choices, null=True, blank=True)
    created_at = models.DateTimeField('creado el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado el', auto_now=True)

    class Meta:
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'
        ordering = ['fecha_hora']

    def __str__(self):
        return f'{self.equipo_local} vs {self.equipo_visitante}'


class Market(models.Model):
    class Tipo(models.TextChoices):
        ONE_X_TWO = 'one_x_two', '1X2'
        OVER_UNDER = 'over_under', 'Over/Under 2.5'
        BTTS = 'btts', 'Ambos Marcan (BTTS)'
        ASIAN_HANDICAP = 'asian_handicap', 'Hándicap Asiático'

    class Estado(models.TextChoices):
        OPEN = 'open', 'Abierto'
        SUSPENDED = 'suspended', 'Suspendido'
        SETTLED = 'settled', 'Liquidado'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='markets')
    tipo = models.CharField('tipo', max_length=20, choices=Tipo.choices, default=Tipo.ONE_X_TWO)
    cuota_local = models.DecimalField('cuota local', max_digits=10, decimal_places=4)
    cuota_empate = models.DecimalField('cuota empate', max_digits=10, decimal_places=4, null=True, blank=True)
    cuota_visitante = models.DecimalField('cuota visitante', max_digits=10, decimal_places=4)
    margen = models.DecimalField('margen', max_digits=6, decimal_places=4, default=0.05)
    estado = models.CharField('estado', max_length=10, choices=Estado.choices, default=Estado.OPEN)
    created_at = models.DateTimeField('creado el', auto_now_add=True)
    updated_at = models.DateTimeField('actualizado el', auto_now=True)

    class Meta:
        verbose_name = 'mercado'
        verbose_name_plural = 'mercados'

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.event}'
