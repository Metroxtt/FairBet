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
    return render(request, 'wallet/index.html', {'account': account, 'transactions': transactions, 'page_title': 'Mi Billetera'})


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
        LedgerEntry.objects.create(account=from_account, credit=1000000, description='Fondo inicial Casa')
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
        LedgerEntry.objects.create(account=to_account, credit=1000000, description='Fondo inicial Casa')

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
