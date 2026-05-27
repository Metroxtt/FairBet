from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Account, LedgerEntry, transfer
from .serializers import AccountSerializer, LedgerEntrySerializer, DepositSerializer,withdrawSerializer
from users.models import DepositLimit


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

    limits, _ = DepositLimit.objects.get_or_create(user=user)
    if amount>limits.daily_limit:
        return Response({'error': 'Supera el límite diario'}, status=status.HTTP_400_BAD_REQUEST)

    from_account, _ = Account.objects.get_or_create(
        account_type=Account.Tipo.CASA,
        defaults={'balance': 1000000}
    )
    to_account, _ = Account.objects.get_or_create(
        user=user,
        account_type=Account.Tipo.WALLET_USUARIO
    )

    try:
        transfer(from_account, to_account, amount, f'Depósito de {user}',
                 idempotency_key=idempotency_key)
        to_account.refresh_from_db()
        return Response({''
        'mensaje': 'Depósito exitoso',
          'saldo': to_account.balance,
          'footer': 'Esta es un plataforma educativa con moneda NO real. No se consituye como una casa de apuestas.',
          })
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes[permissions.IsAuthenticated]
def withdraw(request):
    serializer= withdrawSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = request.user
    amount = serializer.validated_data['amount']
    idempotency_key= serializer.validated_data.get('idempotency_key')

    if user.is_excluded:
        return Response({'Error': 'Usuario excluido automaticamente, no podrá realizar retiros'},
                        status=status.HTTP_403_FORBIDDEN)
    
    from_account = Account.objects.get(
        user=user,
        account_type=Account.Tipo.WALLET_USUARIO
    )
    to_account = Account.objects.get(
        account_type = Account.Tipo.CASA
    )

    try:
        transfer(from_account, to_account, amount, f'Retiro de {user}',
                 idempotency_key=idempotency_key)
        return Response({
            'mensaje': 'Retiro Exitoso',
            'saldo': from_account.balance,
            'footer': 'Plataforma educativa con moneda virtual. No constituye una casa de apuestas.',
        })
    except ValueError as e:
        return Response ({'Error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
