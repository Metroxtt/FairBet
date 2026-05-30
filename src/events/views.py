from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Event, Market
from .serializers import EventSerializer, MarketSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['estado']
    search_fields = ['equipo_local', 'equipo_visitante']

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def simulate_critical_event(self, request, pk=None):
        event = self.get_object()
        
        # Pasar a LIVE si estaba programado
        if event.estado == Event.Estado.SCHEDULED:
            event.estado = Event.Estado.LIVE
            event.save(update_fields=['estado'])
            
        markets = event.markets.filter(estado=Market.Estado.OPEN)
        count = 0
        for market in markets:
            market.estado = Market.Estado.SUSPENDED
            market.save(update_fields=['estado'])
            count += 1
            # Importación local para evitar circular imports
            from .tasks import restore_market_status
            restore_market_status.apply_async(args=[market.pk], countdown=10)
            
        return Response({
            'mensaje': f'Simulación iniciada. {count} mercados suspendidos por 10s.',
            'event_status': event.estado
        })


from django.shortcuts import render

class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['event', 'estado', 'tipo']

def event_list_view(request):
    events = Event.objects.all().order_by('fecha_hora').prefetch_related('markets')
    return render(request, 'events/list.html', {'events': events, 'page_title': 'Eventos'})
