import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Event, Market


class OddsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.group_name = f'odds_{self.event_id}'

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        event_data = await self.get_event_data()
        if event_data:
            await self.send(text_data=json.dumps(event_data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def odds_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def get_event_data(self):
        try:
            event = Event.objects.get(pk=self.event_id)
            markets = Market.objects.filter(event=event)
            return {
                'type': 'odds_snapshot',
                'event_id': str(event.pk),
                'equipo_local': event.equipo_local,
                'equipo_visitante': event.equipo_visitante,
                'estado': event.estado,
                'markets': [
                    {
                        'id': str(m.pk),
                        'tipo': m.tipo,
                        'cuota_local': str(m.cuota_local),
                        'cuota_empate': str(m.cuota_empate) if m.cuota_empate else None,
                        'cuota_visitante': str(m.cuota_visitante),
                        'estado': m.estado,
                    }
                    for m in markets
                ],
            }
        except Event.DoesNotExist:
            return None
