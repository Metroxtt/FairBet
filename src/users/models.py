from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class EstadoUser(models.TextChoices):
    PENDIENTE_VERIFICACION = 'pendiente_verificacion', 'Pendiente de Verificación'
    VERIFICADO = 'verificado', 'Verificado'
    BLOQUEADO = 'bloqueado', 'Bloqueado'
    AUTOEXCLUIDO = 'autoexcluido', 'Autoexcluido'

class UserManager(BaseUserManager):
    def create_user(self, email, dni, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        if not dni:
            raise ValueError('El DNI es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, dni, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('estado', EstadoUser.VERIFICADO)
        return self.create_user(email, dni, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    dni = models.CharField('DNI', max_length=8, unique=True)
    email = models.EmailField('correo electrónico', unique=True)
    nombre = models.CharField('nombres', max_length=100)
    apellido = models.CharField('apellidos', max_length=100)
    telefono = models.CharField('teléfono', max_length=15, blank=True)
    fecha_nacimiento = models.DateField('fecha de nacimiento')

    estado = models.CharField(
        'estado', max_length=25, 
        choices=EstadoUser.choices, 
        default=EstadoUser.PENDIENTE_VERIFICACION)
    
    fecha_exclusion = models.DateTimeField('fecha de autoexclusión', null=True, blank=True)
    fecha_fin_exclusion = models.DateTimeField('fin de autoexclusión', null=True, blank=True)
    
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField('fecha de registro', auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['dni', 'nombre', 'apellido', 'fecha_nacimiento']

    class Meta:
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        return f'{self.nombre} {self.apellido} - {self.dni}'

    @property
    def edad(self):
        from datetime import date
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    @property
    def es_mayor_de_edad(self):
        return self.edad >= 18
    
    @property
    def es_verificado(self):
        return self.estado == EstadoUser.VERIFICADO
    
    @property
    def esta_autoexcluido(self):
        return self.estado == EstadoUser.AUTOEXCLUIDO


class DepositLimit(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='deposit_limit',
        verbose_name='usuario'
    )
    daily_limit = models.DecimalField('límite diario', max_digits=18, decimal_places=4, default=500)
    weekly_limit = models.DecimalField('límite semanal', max_digits=18, decimal_places=4, default=2000)
    monthly_limit = models.DecimalField('límite mensual', max_digits=18, decimal_places=4, default=5000)
    updated_at = models.DateTimeField('actualizado el', auto_now=True)

    class Meta:
        verbose_name = 'límite de depósito'
        verbose_name_plural = 'límites de depósito'

    def __str__(self):
        return f'Límites de {self.user}'
