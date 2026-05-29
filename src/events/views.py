from rest_framework import viewsets, permissions, filters
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


from django.shortcuts import render

class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['event', 'estado', 'tipo']

def event_list_view(request):
    events = Event.objects.all().order_by('fecha_hora')
    return render(request, 'events/list.html', {'events': events, 'page_title': 'Eventos'})
