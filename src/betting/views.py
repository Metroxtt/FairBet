import uuid
from decimal import Decimal
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from events.models import Event, Market
from wallet.models import Account, transfer
from .models import Bet, ComboBet, ComboLeg
from .serializers import BetSerializer, PlaceBetSerializer, ComboBetSerializer, PlaceComboBetSerializer

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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def place_combo_bet(request):
    serializer = PlaceComboBetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    idemp_key = request.headers.get('X-Idempotency-Key') or serializer.validated_data.get('idempotency_key')
    if idemp_key:
        from django.core.cache import cache
        cache_key = f'idemp_combo_{idemp_key}'
        if cache.get(cache_key):
            return Response({'error': 'Solicitud duplicada. Esta apuesta combinada ya fue procesada.'}, status=status.HTTP_409_CONFLICT)
        cache.set(cache_key, True, timeout=86400)
        
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

    legs_data = serializer.validated_data['legs']
    monto = serializer.validated_data['monto']
    
    # Validar y extraer eventos/mercados
    cuota_total = Decimal('1.0000')
    event_market_objs = []
    
    for leg in legs_data:
        try:
            event = Event.objects.get(pk=leg['event_id'])
            market = Market.objects.get(pk=leg['market_id'])
        except (Event.DoesNotExist, Market.DoesNotExist):
            return Response({'error': f"Evento {leg['event_id']} o mercado {leg['market_id']} no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
        if event.estado not in [Event.Estado.SCHEDULED, Event.Estado.LIVE]:
            return Response({'error': f"El evento {event.id} no esta disponible"}, status=status.HTTP_400_BAD_REQUEST)
            
        if market.estado != Market.Estado.OPEN:
            return Response({'error': f"Mercado {market.id} no disponible"}, status=status.HTTP_400_BAD_REQUEST)
            
        seleccion = leg['seleccion']
        cuota_map = {
            'local': market.cuota_local,
            'empate': market.cuota_empate,
            'visita': market.cuota_visitante,
        }
        cuota = cuota_map.get(seleccion)
        if not cuota:
            return Response({'error': f"Seleccion {seleccion} invalida para el evento {event.id}"}, status=status.HTTP_400_BAD_REQUEST)
            
        cuota_esperada = leg.get('cuota_esperada')
        if cuota_esperada and cuota != cuota_esperada:
            return Response({
                'error': f'La cuota del evento {event.id} ha cambiado.',
                'codigo': 'RE_COTIZACION',
                'event_id': event.id,
                'nueva_cuota': str(cuota)
            }, status=status.HTTP_409_CONFLICT)
            
        cuota_total *= cuota
        event_market_objs.append({
            'event': event,
            'market': market,
            'seleccion': seleccion,
            'cuota': cuota
        })

    from_account, _ = Account.objects.get_or_create(
        user=user, account_type=Account.Tipo.WALLET_USUARIO
    )
    to_account, _ = Account.objects.get_or_create(
        account_type=Account.Tipo.APUESTAS_PENDIENTES
    )

    if from_account.balance < monto:
        return Response({'error': 'Saldo insuficiente para realizar la apuesta combinada'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from wallet.models import transfer
        transfer(from_account, to_account, monto, f'Apuesta Combinada ({len(legs_data)} selecciones)', idempotency_key=idemp_key)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    import uuid
    combo_bet = ComboBet.objects.create(
        user=user, 
        monto=monto, 
        cuota_total=round(cuota_total, 4),
        idempotency_key=idemp_key if idemp_key else uuid.uuid4()
    )
    
    for obj in event_market_objs:
        ComboLeg.objects.create(
            combo=combo_bet,
            event=obj['event'],
            market=obj['market'],
            seleccion=obj['seleccion'],
            cuota=obj['cuota']
        )
        
    if monto >= Decimal('2000'):
        from .models import SuspiciousActivity
        SuspiciousActivity.objects.create(
            user=user,
            motivo=f'Apuesta combinada inusualmente alta de {monto} fichas.',
            severidad=SuspiciousActivity.Severidad.ALTA
        )

    return Response(ComboBetSerializer(combo_bet).data, status=status.HTTP_201_CREATED)


from django.db import transaction

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_settle_event(request):
    """
    Settle an event, resolve all its bets and combo bets.
    Accepts: event_id, resultado ('local', 'empate', 'visita', 'cancelado')
    """
    event_id = request.data.get('event_id')
    resultado = request.data.get('resultado')
    
    if not event_id or not resultado:
        return Response({'error': 'Faltan parámetros: event_id y resultado son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if resultado not in ['local', 'empate', 'visita', 'cancelado']:
        return Response({'error': 'Resultado inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
    if event.estado == Event.Estado.FINISHED or event.estado == Event.Estado.CANCELLED:
        return Response({'error': 'El evento ya ha sido finalizado o cancelado anteriormente.'}, status=status.HTTP_400_BAD_REQUEST)
        
    with transaction.atomic():
        if resultado == 'cancelado':
            event.estado = Event.Estado.CANCELLED
        else:
            event.estado = Event.Estado.FINISHED
            event.resultado = resultado
        event.save()
        
        event.markets.all().update(estado=Market.Estado.SETTLED)
        
        bets = Bet.objects.filter(event=event, estado=Bet.Estado.PENDING)
        for bet in bets:
            bet.settle(resultado)
            
        combo_bets = ComboBet.objects.filter(legs__event=event, estado=ComboBet.Estado.PENDING).distinct()
        for combo in combo_bets:
            combo.check_and_settle()
            
    return Response({'mensaje': 'Evento liquidado exitosamente.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_suspend_market(request):
    """
    Suspend or unsuspend a market or the entire event.
    Accepts: event_id, market_id (optional), action ('suspend', 'unsuspend')
    """
    event_id = request.data.get('event_id')
    market_id = request.data.get('market_id')
    action = request.data.get('action') # 'suspend' or 'unsuspend'
    
    if not event_id or not action:
        return Response({'error': 'Faltan parámetros: event_id y action son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
        
    if action not in ['suspend', 'unsuspend']:
        return Response({'error': 'Acción inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return Response({'error': 'Evento no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        
    if market_id:
        try:
            market = Market.objects.get(pk=market_id, event=event)
        except Market.DoesNotExist:
            return Response({'error': 'Mercado no encontrado.'}, status=status.HTTP_404_NOT_FOUND)
            
        if action == 'suspend':
            market.estado = Market.Estado.SUSPENDED
        else:
            market.estado = Market.Estado.OPEN
        market.save()
        return Response({'mensaje': f"Mercado {market_id} {'suspendido' if action == 'suspend' else 'habilitado'} exitosamente."}, status=status.HTTP_200_OK)
    else:
        if action == 'suspend':
            event.estado = Event.Estado.SUSPENDED
            event.markets.all().update(estado=Market.Estado.SUSPENDED)
        else:
            from django.utils import timezone
            if event.fecha_hora > timezone.now():
                event.estado = Event.Estado.SCHEDULED
            else:
                event.estado = Event.Estado.LIVE
            event.markets.all().update(estado=Market.Estado.OPEN)
        event.save()
        return Response({'mensaje': f"Evento {event_id} {'suspendido' if action == 'suspend' else 'habilitado'} exitosamente."}, status=status.HTTP_200_OK)
