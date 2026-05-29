from django.test import TestCase
from decimal import Decimal
from .models import User, DepositLimit, EstadoUser
from django.utils import timezone
from datetime import timedelta
from .serializers import DepositLimitSerializer, UserSerializer, RegisterSerializer

class UserModelTest(TestCase):
    def test_crear_usuario_valido(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678',
            nombre='Test',
            apellido='User',
            fecha_nacimiento='2000-01-01',
            password='testpass123'
        )
        self.assertEqual(user.estado, EstadoUser.PENDIENTE_VERIFICACION)
        self.assertTrue(user.es_mayor_de_edad)
        self.assertEqual(str(user), 'Test User - 12345678')
        
    def test_usuario_creado_con_deposit_limit(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        self.assertTrue(hasattr(user, 'deposit_limit'))
        self.assertEqual(user.deposit_limit.daily_limit, Decimal('500'))
        
    def test_edad_property(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        hoy= timezone.now().date()
        esperada = hoy.year - 2000 - ((hoy.month, hoy.day) < (1, 1))
        self.assertEqual(user.edad, esperada)
        
    def test_es_mayor_de_edad_con_18(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2006-05-27', password='testpass123'
        )
        self.assertTrue(user.es_mayor_de_edad)
        
    def test_es_mayor_de_edad_con_17(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2009-05-27', password='testpass123'
        )
        self.assertFalse(user.es_mayor_de_edad)
        
    def test_es_verificado_property(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        self.assertFalse(user.es_verificado)
        user.estado = EstadoUser.VERIFICADO
        self.assertTrue(user.es_verificado)
        
    def test_autoexclusion_7_dias(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        user.estado = EstadoUser.AUTOEXCLUIDO
        user.fecha_exclusion = timezone.now()
        user.fecha_fin_exclusion = timezone.now() + timedelta(days=7)
        self.assertTrue(user.esta_autoexcluido)
        self.assertIsNotNone(user.fecha_fin_exclusion)
    
    def test_autoexclusion_indefinida(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        user.estado = EstadoUser.AUTOEXCLUIDO
        user.fecha_exclusion = timezone.now()
        user.fecha_fin_exclusion = None
        self.assertTrue(user.esta_autoexcluido)
        self.assertIsNone(user.fecha_fin_exclusion)    
        
    def test_esta_autoexcluido_property(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        self.assertFalse(user.esta_autoexcluido)
        user.estado = EstadoUser.AUTOEXCLUIDO
        self.assertTrue(user.esta_autoexcluido)
        
    def test_cooldown_subir_limite(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        limite = user.deposit_limit
        limite.daily_limit = 100
        limite.cooldown_hasta = timezone.now() + timedelta(hours=24)
        limite.save()
        
        data = {'daily_limit': 500}
        serializer = DepositLimitSerializer(
            instance=limite, data=data, partial=True,
            context={'request': type('Req', (), {'user': user})()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('daily_limit', serializer.errors)
        
class UserSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
    def test_estado_es_read_only(self):
        data = {'estado': EstadoUser.VERIFICADO}
        serializer = UserSerializer(instance=self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.estado, EstadoUser.PENDIENTE_VERIFICACION)    
        
class RegisterSerializerTest(TestCase):
    def test_dni_invalido_rechaza(self):
        data = {
            'dni': '12345678A',
            'email': 'test@test.com',
            'nombre': 'Test', 'apellido': 'User',
            'fecha_nacimiento': '2000-01-01',
            'password': 'testpass123',
            'confirmar_password': 'testpass123',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('dni', serializer.errors)
    def test_dni_con_digito_verificador_incorrecto_rechaza(self):
        data = {
            'dni': '12345679',
            'email': 'test@test.com',
            'nombre': 'Test', 'apellido': 'User',
            'fecha_nacimiento': '2000-01-01',
            'password': 'testpass123',
            'confirmar_password': 'testpass123',
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('dni', serializer.errors)
    def test_autoexcluido_no_puede_cambiar_limite(self):
        user = User.objects.create_user(
            email='autoexcluido@test.com',
            dni='12345678', nombre='Auto', apellido='Excluido',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        user.estado = EstadoUser.AUTOEXCLUIDO
        user.save()
        limite = user.deposit_limit
        data = {'daily_limit': 100}
        serializer = DepositLimitSerializer(
            instance=limite, data=data, partial=True,
            context={'request': type('Req', (), {'user': user})()}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        
    def test_autoexcluir_ya_autoexcluido_rechaza(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status
        from .views import self_exclude
        user = User.objects.create_user(
            email='yaautoexcluido@test.com',
            dni='12345678', nombre='Ya', apellido='Autoexcluido',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        user.estado = EstadoUser.AUTOEXCLUIDO
        user.fecha_exclusion = timezone.now()
        user.save()
        factory = APIRequestFactory()
        request = factory.post('/self-exclude/', {'plazo': 'indefinido'})
        force_authenticate(request, user=user)
        response = self_exclude(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_kyc_exitoso(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status
        from .views import verify_kyc
        user = User.objects.create_user(
            email='pendiente@test.com',
            dni='12345678', nombre='Pendiente', apellido='Test',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        self.assertEqual(user.estado, EstadoUser.PENDIENTE_VERIFICACION)
        factory = APIRequestFactory()
        request = factory.post('/verify-kyc/', {'confirmar': True}, format='json')
        force_authenticate(request, user=user)
        response = verify_kyc(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertEqual(user.estado, EstadoUser.VERIFICADO)

    def test_verify_kyc_ya_verificado_rechaza(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status
        from .views import verify_kyc
        user = User.objects.create_user(
            email='yaverificado@test.com',
            dni='12345678', nombre='Ya', apellido='Verificado',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        user.estado = EstadoUser.VERIFICADO
        user.save()
        factory = APIRequestFactory()
        request = factory.post('/verify-kyc/', {'confirmar': True}, format='json')
        force_authenticate(request, user=user)
        response = verify_kyc(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_kyc_sin_confirmar_rechaza(self):
        from rest_framework.test import APIRequestFactory, force_authenticate
        from rest_framework import status
        from .views import verify_kyc
        user = User.objects.create_user(
            email='sconfirmar@test.com',
            dni='12345678', nombre='Sin', apellido='Confirmar',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        factory = APIRequestFactory()
        request = factory.post('/verify-kyc/', {'confirmar': False}, format='json')
        force_authenticate(request, user=user)
        response = verify_kyc(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cooldown_hasta_al_subir_limite(self):
        user = User.objects.create_user(
            email='cooldown@test.com',
            dni='12345678', nombre='Cooldown', apellido='Test',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        limite = user.deposit_limit
        data = {'daily_limit': 1000}
        serializer = DepositLimitSerializer(
            instance=limite, data=data, partial=True,
            context={'request': type('Req', (), {'user': user})()}
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        limite.refresh_from_db()
        self.assertIsNotNone(limite.cooldown_hasta)
        self.assertTrue(limite.cooldown_hasta > timezone.now())