from .models import User, DepositLimit, EstadoUser
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .serializers import RegisterSerializer, UserSerializer, DepositLimitSerializer


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

    user.estado = EstadoUser.AUTOEXCLUIDO
    user.save(update_fields=['estado'])

    return Response({'mensaje': 'Usuario autoexcluido correctamente'}, status=status.HTTP_200_OK)
