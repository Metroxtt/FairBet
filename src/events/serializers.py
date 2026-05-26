from rest_framework import serializers
from .models import Event, Market


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    markets = MarketSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
