from celery import shared_task
from events.models import Event


@shared_task
def settle_bets_for_event(event_id):
    from .models import Bet
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return f'Evento {event_id} no encontrado'

    if not event.resultado:
        return f'Evento {event_id} no tiene resultado'

    bets = Bet.objects.filter(event=event, estado=Bet.Estado.PENDING)
    count = 0
    for bet in bets:
        try:
            bet.settle(event.resultado)
            count += 1
        except ValueError:
            continue

    return f'Liquidadas {count} apuestas del evento {event_id}'
