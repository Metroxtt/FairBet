from decimal import Decimal
from rest_framework import serializers
from .models import Bet, ComboBet, ComboLeg


class BetSerializer(serializers.ModelSerializer):
    pago_potencial = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)

    class Meta:
        model = Bet
        fields = ['id', 'user', 'event', 'market', 'seleccion', 'cuota_al_apostar',
                  'monto', 'pago_potencial', 'estado', 'created_at']
        read_only_fields = ['user', 'estado', 'pago_potencial']


class PlaceBetSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    market_id = serializers.IntegerField()
    seleccion = serializers.ChoiceField(choices=['local', 'empate', 'visita'])
    monto = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.01'))
    cuota_esperada = serializers.DecimalField(max_digits=10, decimal_places=4, required=False)
    idempotency_key = serializers.UUIDField(required=False)

class ComboLegSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComboLeg
        fields = ['event', 'market', 'seleccion', 'cuota']


class ComboBetSerializer(serializers.ModelSerializer):
    legs = ComboLegSerializer(many=True)

    class Meta:
        model = ComboBet
        fields = ['id', 'user', 'monto', 'cuota_total', 'estado', 'legs', 'created_at']
        read_only_fields = ['user', 'estado']


class PlaceComboLegSerializer(serializers.Serializer):
    event_id = serializers.IntegerField()
    market_id = serializers.IntegerField()
    seleccion = serializers.ChoiceField(choices=['local', 'empate', 'visita'])
    cuota_esperada = serializers.DecimalField(max_digits=10, decimal_places=4, required=False)


class PlaceComboBetSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.01'))
    idempotency_key = serializers.UUIDField(required=False)
    legs = PlaceComboLegSerializer(many=True, allow_empty=False)

    def validate_legs(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Una apuesta combinada debe tener al menos 2 selecciones.")
        if len(value) > 10:
            raise serializers.ValidationError("No se permiten más de 10 selecciones por apuesta combinada.")
        
        event_ids = [leg['event_id'] for leg in value]
        if len(event_ids) != len(set(event_ids)):
            raise serializers.ValidationError("No puedes hacer selecciones múltiples del mismo evento.")
            
        return value
