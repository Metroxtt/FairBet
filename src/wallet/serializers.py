from decimal import Decimal
from rest_framework import serializers
from .models import Account, LedgerEntry
from decimal import Decimal

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'account_type', 'balance', 'created_at']


class LedgerEntrySerializer(serializers.ModelSerializer):
    account = serializers.StringRelatedField()

    class Meta:
        model = LedgerEntry
        fields = ['id', 'account', 'debit', 'credit', 'balance_after', 'description', 'created_at']


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.01'))
    idempotency_key = serializers.UUIDField(required=False)


class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.01'))
    idempotency_key = serializers.UUIDField(required=False)
