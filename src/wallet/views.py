from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Account, LedgerEntry, transfer
from .serializers import AccountSerializer, LedgerEntrySerializer, DepositSerializer,WithdrawSerializer
from users.models import DepositLimit
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def wallet_index_view(request):
    account, _ = Account.objects.get_or_create(
        user=request.user, account_type=Account.Tipo.WALLET_USUARIO
    )
    transactions = LedgerEntry.objects.filter(account=account).order_by('-created_at')[:20]
    
    from users.models import DepositLimit
    from django.db.models import Sum
    from django.utils import timezone
    from datetime import timedelta
    from decimal import Decimal
    
    limit, _ = DepositLimit.objects.get_or_create(user=request.user)
    
    now = timezone.now()
    start_of_day = now - timedelta(days=1)
    start_of_week = now - timedelta(days=7)
    start_of_month = now - timedelta(days=30)
    
    daily_deposits = LedgerEntry.objects.filter(
        account=account,
        credit__gt=0,
        description__icontains='depósito',
        created_at__gte=start_of_day
    ).aggregate(total=Sum('credit'))['total'] or Decimal('0')

    weekly_deposits = LedgerEntry.objects.filter(
        account=account,
        credit__gt=0,
        description__icontains='depósito',
        created_at__gte=start_of_week
    ).aggregate(total=Sum('credit'))['total'] or Decimal('0')

    monthly_deposits = LedgerEntry.objects.filter(
        account=account,
        credit__gt=0,
        description__icontains='depósito',
        created_at__gte=start_of_month
    ).aggregate(total=Sum('credit'))['total'] or Decimal('0')
    
    daily_remaining = max(Decimal('0'), limit.daily_limit - daily_deposits)
    weekly_remaining = max(Decimal('0'), limit.weekly_limit - weekly_deposits)
    monthly_remaining = max(Decimal('0'), limit.monthly_limit - monthly_deposits)
    
    return render(request, 'wallet/index.html', {
        'account': account,
        'transactions': transactions,
        'page_title': 'Mi Billetera',
        'daily_remaining': daily_remaining,
        'weekly_remaining': weekly_remaining,
        'monthly_remaining': monthly_remaining
    })


class BalanceView(generics.RetrieveAPIView):
    serializer_class = AccountSerializer

    def get_object(self):
        account, _ = Account.objects.get_or_create(
            user=self.request.user,
            account_type=Account.Tipo.WALLET_USUARIO
        )
        return account


class TransactionHistoryView(generics.ListAPIView):
    serializer_class = LedgerEntrySerializer

    def get_queryset(self):
        account = Account.objects.get(
            user=self.request.user,
            account_type=Account.Tipo.WALLET_USUARIO
        )
        return LedgerEntry.objects.filter(account=account)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated]) 
def deposit(request):
    serializer = DepositSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if user.is_staff:
        return Response({'error': 'Los administradores no pueden depositar fichas.'},
                        status=status.HTTP_403_FORBIDDEN)
    
    amount = serializer.validated_data['amount']
    idempotency_key = serializer.validated_data.get('idempotency_key')

    try:
        from .models import check_deposit_limit
        check_deposit_limit(user, amount)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    from_account, created = Account.objects.get_or_create(
        account_type=Account.Tipo.CASA
    )
    if created:
        LedgerEntry.objects.create(account=from_account, credit=10000, description='Fondo inicial Casa')
    to_account, _ = Account.objects.get_or_create(
        user=user,
        account_type=Account.Tipo.WALLET_USUARIO
    )

    try:
        transfer(from_account, to_account, amount, f'Depósito de {user}',
                 idempotency_key=idempotency_key)
        to_account.refresh_from_db()
        return Response({
        'mensaje': 'Depósito exitoso',
          'saldo': to_account.balance,
          'footer': 'Plataforma educativa con moneda virtual. No constituye una casa de apuestas.',
          })
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def withdraw(request):
    serializer= WithdrawSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    if user.is_staff:
        return Response({'error': 'Los administradores no pueden retirar fichas.'},
                        status=status.HTTP_403_FORBIDDEN)
    
    amount = serializer.validated_data['amount']
    idempotency_key= serializer.validated_data.get('idempotency_key')

    if user.esta_autoexcluido:
        return Response({'error': 'Usuario autoexcluido, no puede realizar retiros'},
                        status=status.HTTP_403_FORBIDDEN)

    from_account, _ = Account.objects.get_or_create(
        user=user,
        account_type=Account.Tipo.WALLET_USUARIO
    )
    to_account, created = Account.objects.get_or_create(
        account_type=Account.Tipo.CASA
    )
    if created:
        LedgerEntry.objects.create(account=to_account, credit=10000, description='Fondo inicial Casa')

    try:
        transfer(from_account, to_account, amount, f'Retiro de {user}',
                 idempotency_key=idempotency_key)
        from_account.refresh_from_db()
        return Response({
            'mensaje': 'Retiro Exitoso',
            'saldo': from_account.balance,
            'footer': 'Plataforma educativa con moneda virtual. No constituye una casa de apuestas.',
        })
    except ValueError as e:
        return Response ({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def verify_ledger(request):
    import hashlib
    
    accounts = Account.objects.all()
    inconsistencias = []
    
    for account in accounts:
        entries = LedgerEntry.objects.filter(account=account).order_by('created_at', 'id')
        prev_hash = '0' * 64
        
        for entry in entries:
            # Recalcular hash esperado
            d_str = f"{entry.debit:.4f}"
            c_str = f"{entry.credit:.4f}"
            data = f"{prev_hash}{entry.id}{entry.account_id}{d_str}{c_str}{entry.description}"
            expected_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()
            
            if entry.hash != expected_hash:
                inconsistencias.append({
                    'account_id': str(account.id),
                    'entry_id': str(entry.id),
                    'motivo': 'Hash actual no coincide con el hash calculado',
                    'esperado': expected_hash,
                    'actual': entry.hash
                })
                break
                
            if entry.previous_hash != prev_hash:
                inconsistencias.append({
                    'account_id': str(account.id),
                    'entry_id': str(entry.id),
                    'motivo': 'El previous_hash no coincide con el hash del registro anterior',
                    'esperado': prev_hash,
                    'actual': entry.previous_hash
                })
                break
                
            prev_hash = entry.hash
            
    if inconsistencias:
        return Response({
            'estado': 'inconsistente',
            'errores': inconsistencias
        }, status=status.HTTP_400_BAD_REQUEST)
        
    return Response({
        'estado': 'ok',
        'mensaje': 'Todas las cadenas de hash del ledger son íntegras y válidas.'
    }, status=status.HTTP_200_OK)
