from .models import User, DepositLimit, EstadoUser
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import (
    RegisterSerializer, UserSerializer, DepositLimitSerializer,
    VerifyKYCSerializer,
)
from datetime import timedelta
from django.utils import timezone


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class DepositLimitView(generics.RetrieveUpdateAPIView):
    serializer_class = DepositLimitSerializer

    def get_object(self):
        obj, _ = DepositLimit.objects.get_or_create(user=self.request.user)
        return obj


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def self_exclude(request):
    user = request.user

    if user.esta_autoexcluido:
        return Response(
            {'error': 'Ya estás autoexcluido. No puedes autoexcluirte nuevamente.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    plazo = request.data.get('plazo', 'indefinido')
    user.estado = EstadoUser.AUTOEXCLUIDO
    user.fecha_exclusion = timezone.now()
    if plazo == '7':
        user.fecha_fin_exclusion = timezone.now() + timedelta(days=7)
    elif plazo == '30':
        user.fecha_fin_exclusion = timezone.now() + timedelta(days=30)
    elif plazo == '90':
        user.fecha_fin_exclusion = timezone.now() + timedelta(days=90)
    else:
        user.fecha_fin_exclusion = None
    user.save(update_fields=['estado', 'fecha_exclusion', 'fecha_fin_exclusion'])
    return Response({'mensaje': 'Usuario autoexcluido correctamente'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_kyc(request):
    user = request.user

    if user.estado != EstadoUser.PENDIENTE_VERIFICACION:
        return Response(
            {'error': f'La cuenta ya está en estado: {user.get_estado_display()}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = VerifyKYCSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user.estado = EstadoUser.VERIFICADO
    user.save(update_fields=['estado'])

    return Response(
        {'mensaje': 'Cuenta verificada correctamente', 'estado': user.estado},
        status=status.HTTP_200_OK,
    )