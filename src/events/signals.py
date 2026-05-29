from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Market, Event

@receiver(post_save, sender=Market)
def broadcast_odds_update(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    group_name = f'odds_{instance.event_id}'

    data = {
        'type': 'odds_update',
        'market_id': str(instance.pk),
        'tipo': instance.tipo,
        'cuota_local': str(instance.cuota_local),
        'cuota_empate': str(instance.cuota_empate) if instance.cuota_empate else None,
        'cuota_visitante': str(instance.cuota_visitante),
        'estado': instance.estado,
    }

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'odds_update',
            'data': data
        }
    )


@receiver(post_save, sender=Event)
def auto_settle_bets(sender, instance, **kwargs):
    if instance.estado == Event.Estado.FINISHED and instance.resultado:
        def delay_settle():
            from betting.tasks import settle_bets_for_event
            settle_bets_for_event.delay(instance.pk)
        transaction.on_commit(delay_settle)
