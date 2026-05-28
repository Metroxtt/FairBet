from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from events.models import Event, Market
from wallet.models import Account, transfer
from .models import Bet
from .serializers import BetSerializer, PlaceBetSerializer


class BetHistoryView(generics.ListAPIView):
    serializer_class = BetSerializer

    def get_queryset(self):
        return Bet.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def place_bet(request):
    serializer = PlaceBetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user

    if user.is_excluded:
        return Response({'error': 'Usuario autoexcluido no puede apostar'},
                        status=status.HTTP_403_FORBIDDEN)

    try:
        event = Event.objects.get(pk=serializer.validated_data['event_id'])
        market = Market.objects.get(pk=serializer.validated_data['market_id'])
    except (Event.DoesNotExist, Market.DoesNotExist) as e:
        return Response({'error': 'Evento o mercado no encontrado'},
                        status=status.HTTP_404_NOT_FOUND)

    if market.estado != Market.Estado.OPEN:
        return Response({'error': 'Mercado no disponible'},
                        status=status.HTTP_400_BAD_REQUEST)

    seleccion = serializer.validated_data['seleccion']
    monto = serializer.validated_data['monto']

    cuota_map = {
        'local': market.cuota_local,
        'empate': market.cuota_empate,
        'visita': market.cuota_visitante,
    }

    cuota = cuota_map.get(seleccion)
    if not cuota:
        return Response({'error': 'Selección inválida'},
                        status=status.HTTP_400_BAD_REQUEST)

    from_account = Account.objects.get(user=user, account_type=Account.Tipo.WALLET_USUARIO)
    to_account = Account.objects.get(account_type=Account.Tipo.APUESTAS_PENDIENTES)

    try:
        transfer(from_account, to_account, monto,
                 f'Apuesta {event}', idempotency_key=serializer.validated_data.get('idempotency_key'))
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    bet = Bet.objects.create(
        user=user, event=event, market=market,
        seleccion=seleccion, cuota_al_apostar=cuota, monto=monto
    )

    return Response(BetSerializer(bet).data, status=status.HTTP_201_CREATED)
