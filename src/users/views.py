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
    authentication_classes = []
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

@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_verify_kyc(request):
    user_id = request.data.get('user_id')
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if user.estado != EstadoUser.PENDIENTE_VERIFICACION:
        return Response({'error': f'El usuario ya está en estado: {user.get_estado_display()}'},
                        status=status.HTTP_400_BAD_REQUEST)
    user.estado = EstadoUser.VERIFICADO
    user.save(update_fields=['estado'])
    return Response({'mensaje': f'KYC de {user.email} verificado'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_block_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    if user.is_staff:
        return Response({'error': 'No puedes bloquear a otro administrador'}, status=status.HTTP_403_FORBIDDEN)
    user.estado = EstadoUser.BLOQUEADO
    user.save(update_fields=['estado'])
    return Response({'mensaje': f'Usuario {user.email} bloqueado'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAdminUser])
def admin_unblock_user(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    user.estado = EstadoUser.PENDIENTE_VERIFICACION
    user.save(update_fields=['estado'])
    return Response({'mensaje': f'Usuario {user.email} desbloqueado'}, status=status.HTTP_200_OK)