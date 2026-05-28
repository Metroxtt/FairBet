import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from events.models import Event, Market

class Command(BaseCommand):
    help = 'Carga partidos del Mundial 2026 y mercados iniciales.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Eliminando eventos anteriores...')
        Event.objects.all().delete()

        partidos = [
            ('Perú', 'Brasil'),
            ('Argentina', 'Uruguay'),
            ('España', 'Alemania'),
            ('Francia', 'Inglaterra'),
            ('México', 'Colombia')
        ]

        now = timezone.now()
        
        for i, (local, visita) in enumerate(partidos):
            fecha = now + timedelta(days=i+1)
            event = Event.objects.create(
                equipo_local=local,
                equipo_visitante=visita,
                fecha_hora=fecha,
                estado=Event.Estado.SCHEDULED
            )
            
            # Crear mercado 1X2
            Market.objects.create(
                event=event,
                tipo=Market.Tipo.ONE_X_TWO,
                cuota_local=round(random.uniform(1.5, 3.5), 2),
                cuota_empate=round(random.uniform(2.5, 4.0), 2),
                cuota_visitante=round(random.uniform(2.0, 5.0), 2),
                estado=Market.Estado.OPEN
            )
            
            self.stdout.write(self.style.SUCCESS(f'Evento creado: {local} vs {visita}'))
            
        self.stdout.write(self.style.SUCCESS('Todos los eventos y mercados han sido cargados exitosamente.'))
