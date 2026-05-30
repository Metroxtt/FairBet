import uuid
from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from events.models import Event, Market
from wallet.models import Account, transfer
from .models import Bet
from .serializers import BetSerializer, PlaceBetSerializer

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def betting_history_view(request):
    bets = Bet.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'betting/history.html', {'bets': bets, 'page_title': 'Mis Apuestas'})


class BetHistoryView(generics.ListAPIView):
    serializer_class = BetSerializer

    def get_queryset(self):
        return Bet.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def place_bet(request):
    serializer = PlaceBetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # 1. Idempotency Key
    idemp_key = request.headers.get('X-Idempotency-Key') or serializer.validated_data.get('idempotency_key')
    if idemp_key:
        from django.core.cache import cache
        cache_key = f'idemp_bet_{idemp_key}'
        if cache.get(cache_key):
            return Response({'error': 'Solicitud duplicada. Esta apuesta ya fue procesada.'}, status=status.HTTP_409_CONFLICT)
        cache.set(cache_key, True, timeout=86400) # 24 horas de protección

    user = request.user
    
    if user.is_staff:
        return Response({'error': 'Los administradores no pueden apostar en su propia plataforma.'},
                        status=status.HTTP_403_FORBIDDEN)

    if not user.es_verificado:
        return Response({'error': 'Debe verificar su cuenta KYC antes de apostar'},
                        status=status.HTTP_403_FORBIDDEN)

    if user.esta_autoexcluido:
        return Response({'error': 'Usuario autoexcluido no puede apostar'},
                        status=status.HTTP_403_FORBIDDEN)

    try:
        event = Event.objects.get(pk=serializer.validated_data['event_id'])
        market = Market.objects.get(pk=serializer.validated_data['market_id'])
    except (Event.DoesNotExist, Market.DoesNotExist) as e:
        return Response({'error': 'Evento o mercado no encontrado'},
                        status=status.HTTP_404_NOT_FOUND)

    if event.estado not in [Event.Estado.SCHEDULED, Event.Estado.LIVE]:
        return Response({'error': 'El evento no esta disponible para apuestas'},
                        status=status.HTTP_400_BAD_REQUEST)

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
        return Response({'error': 'Seleccion invalida'},
                        status=status.HTTP_400_BAD_REQUEST)
                        
    # 2. Política de re-cotización
    cuota_esperada = serializer.validated_data.get('cuota_esperada')
    if cuota_esperada and cuota != cuota_esperada:
        return Response({
            'error': 'La cuota ha cambiado.',
            'codigo': 'RE_COTIZACION',
            'nueva_cuota': str(cuota)
        }, status=status.HTTP_409_CONFLICT)

    from_account, _ = Account.objects.get_or_create(
        user=user, account_type=Account.Tipo.WALLET_USUARIO
    )
    to_account, _ = Account.objects.get_or_create(
        account_type=Account.Tipo.APUESTAS_PENDIENTES
    )

    if from_account.balance < monto:
        return Response({'error': 'Saldo insuficiente para realizar la apuesta'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        transfer(from_account, to_account, monto,
                 f'Apuesta {event}', idempotency_key=serializer.validated_data.get('idempotency_key'))
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    bet = Bet.objects.create(
        user=user, event=event, market=market,
        seleccion=seleccion, cuota_al_apostar=cuota, monto=monto,
        idempotency_key=idemp_key if idemp_key else uuid.uuid4()
    )
    
    # 3. Anti-fraude básico
    if monto >= Decimal('2000'):
        from .models import SuspiciousActivity
        SuspiciousActivity.objects.create(
            user=user,
            motivo=f'Apuesta inusualmente alta de {monto} fichas.',
            severidad=SuspiciousActivity.Severidad.ALTA
        )

    return Response(BetSerializer(bet).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cashout_bet(request, bet_id):
    try:
        bet = Bet.objects.get(pk=bet_id, user=request.user)
    except Bet.DoesNotExist:
        return Response({'error': 'Apuesta no encontrada'}, status=status.HTTP_404_NOT_FOUND)

    try:
        monto = bet.cash_out()
        return Response({
            'mensaje': 'Cash-out exitoso',
            'monto_devuelto': str(monto)
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
