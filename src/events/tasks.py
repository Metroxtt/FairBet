from celery import shared_task
from .models import Market

@shared_task
def restore_market_status(market_id):
    try:
        market = Market.objects.get(pk=market_id)
        if market.estado == Market.Estado.SUSPENDED:
            market.estado = Market.Estado.OPEN
            market.save(update_fields=['estado'])
    except Market.DoesNotExist:
        pass
