from rest_framework import serializers
from .models import User, DepositLimit


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirmar_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['dni', 'email', 'nombre', 'apellido', 'telefono',
                'fecha_nacimiento', 'password', 'confirmar_password']

    def validate_dni(self, value):
        if not value.isdigit() or len(value) != 8:
            raise serializers.ValidationError('El DNI debe tener 8 dígitos numéricos')
        pesos = [3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(d) * p for d, p in zip(value, pesos))
        digito_esperado = 11 - (suma % 11)
        if digito_esperado == 11:
            digito_esperado = 0
        elif digito_esperado == 10:
            digito_esperado = 1
        if digito_esperado != int(value[-1]):
            raise serializers.ValidationError('El DNI no es válido')
        return value

    def validate_fecha_nacimiento(self, value):
        from datetime import date
        hoy = date.today()
        edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))
        if edad < 18:
            raise serializers.ValidationError('Debe ser mayor de 18 años')
        return value

    def validate(self, data):
        if data['password'] != data['confirmar_password']:
            raise serializers.ValidationError({'confirmar_password': 'Las contraseñas no coinciden'})
        return data

    def create(self, validated_data):
        validated_data.pop('confirmar_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        DepositLimit.objects.create(user=user)
        return user


class UserSerializer(serializers.ModelSerializer):
    edad = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'dni', 'email', 'nombre', 'apellido', 'telefono',
                'fecha_nacimiento', 'edad', 'estado', 'date_joined']


class DepositLimitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositLimit
        fields = ['daily_limit', 'weekly_limit', 'monthly_limit', 'updated_at']
