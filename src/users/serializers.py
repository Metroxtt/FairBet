from django.utils import timezone
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
        if not value.isdigit() or len(value) != 9:
            raise serializers.ValidationError('El DNI debe tener 8 digitos + su codigo de verificacion numéricos')
        pesos = [3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(d) * p for d, p in zip(value[:8], pesos))
        resto = suma % 11
        digito = 11 - resto
        if digito == 11:
            digito = 0
        digito += 1
        serie = "67890112345"
        digito_esperado= serie[digito - 1]
        if digito_esperado != value[-1]:
            raise serializers.ValidationError('El DNI no es válido')
        return value

    def validate_telefono(self, value):
        if not value:
            raise serializers.ValidationError('El teléfono es obligatorio')
        if not value.isdigit() or len(value) != 9 or value[0] != '9':
            raise serializers.ValidationError('El teléfono debe tener 9 dígitos y empezar con 9')
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
                'fecha_nacimiento', 'edad', 'estado', 'date_joined', 'is_active']
        read_only_fields = ['estado', 'is_active']


class DepositLimitSerializer(serializers.ModelSerializer):
    en_cooldown = serializers.SerializerMethodField()

    class Meta:
        model = DepositLimit
        fields = ['daily_limit', 'weekly_limit', 'monthly_limit',
                  'cooldown_hasta', 'en_cooldown', 'updated_at']
        read_only_fields = ['cooldown_hasta', 'en_cooldown', 'updated_at']

    def get_en_cooldown(self, obj):
        return bool(obj.cooldown_hasta and obj.cooldown_hasta > timezone.now())

    def validate(self, data):
        user = self.context['request'].user

        if user.esta_autoexcluido:
            raise serializers.ValidationError(
                'No puedes cambiar tus límites mientras estés autoexcluido'
            )

        instance = self.instance
        for campo in ['daily_limit', 'weekly_limit', 'monthly_limit']:
            if campo in data and instance:
                nuevo_valor = data[campo]
                valor_actual = getattr(instance, campo)
                if nuevo_valor > valor_actual and self.get_en_cooldown(instance):
                    raise serializers.ValidationError({
                        campo: (
                            f'Deben pasar 24h para subir este límite. '
                            f'Válido desde {instance.cooldown_hasta.strftime("%d/%m/%Y %H:%M")}'
                        )
                    })
        return data

    def update(self, instance, validated_data):
        for campo in ['daily_limit', 'weekly_limit', 'monthly_limit']:
            if (
                campo in validated_data
                and validated_data[campo] > getattr(instance, campo)
            ):
                validated_data['cooldown_hasta'] = timezone.now() + timezone.timedelta(hours=24)
                break
        return super().update(instance, validated_data)


class VerifyKYCSerializer(serializers.Serializer):
    confirmar = serializers.BooleanField(write_only=True)

    def validate_confirmar(self, value):
        if not value:
            raise serializers.ValidationError('Debe confirmar la verificación KYC')
        return value