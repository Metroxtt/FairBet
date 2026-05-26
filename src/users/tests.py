"""
Tests para la app users (Raiza).
Basado en: Sesión 05 (pytest, DRF testing)
"""
from django.test import TestCase
from .models import User


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
        self.assertTrue(user.es_mayor_de_edad)
        self.assertTrue(user.is_active)
        self.assertEqual(str(user), 'Test User - 12345678')
