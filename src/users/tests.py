from django.test import TestCase
from decimal import Decimal
from .models import User, DepositLimit, EstadoUser
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
        self.assertEqual(user.edad, 26)
        
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
        
    def test_esta_autoexcluido_property(self):
        user = User.objects.create_user(
            email='test@example.com',
            dni='12345678', nombre='Test', apellido='User',
            fecha_nacimiento='2000-01-01', password='testpass123'
        )
        self.assertFalse(user.esta_autoexcluido)
        user.estado = EstadoUser.AUTOEXCLUIDO
        self.assertTrue(user.esta_autoexcluido)