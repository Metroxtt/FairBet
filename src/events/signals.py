from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Market

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
