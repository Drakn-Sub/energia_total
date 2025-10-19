"""
Tests completos para el sistema de gestión de reservas
Valida requerimientos funcionales y no funcionales
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal

from .models import Socio, Instructor, Clase, Reserva, ListaEspera, TipoClase, Sala
from .services import ReservaService, CuposService, ReservaValidator


class ModelosTestCase(TestCase):
    """Tests de modelos y validaciones"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        # Crear usuario y socio
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.socio = Socio.objects.create(
            user=self.user,
            rut='12345678-9',
            numero_socio='SOC001',
            fecha_inicio_membresia=date.today() - timedelta(days=30),
            fecha_fin_membresia=date.today() + timedelta(days=30),
            estado_membresia='activa'
        )
        
        # Crear instructor
        instructor_user = User.objects.create_user(
            username='instructor',
            password='pass123',
            first_name='Instructor',
            last_name='Test'
        )
        
        self.instructor = Instructor.objects.create(
            user=instructor_user,
            especialidades='Yoga',
            fecha_contratacion=date.today()
        )
        
        # Crear sala
        self.sala = Sala.objects.create(
            nombre='Sala 1',
            capacidad_maxima=20,
            tipo_sala='yoga'
        )
        
        # Crear clase
        self.clase = Clase.objects.create(
            nombre='Yoga Test',
            descripcion='Clase de prueba',
            tipo='yoga',
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(10, 0),
            duracion=timedelta(hours=1),
            capacidad=10,
            instructor=self.instructor,
            instructor_nombre='Instructor Test',
            sala=self.sala,
            precio=Decimal('25000.00')
        )
    
    def test_socio_membresia_vigente(self):
        """Test RF-001: Validación de membresía vigente"""
        self.assertTrue(self.socio.membresia_vigente())
    
    def test_socio_membresia_vencida(self):
        """Test RF-001: Membresía vencida debe retornar False"""
        self.socio.fecha_fin_membresia = date.today() - timedelta(days=1)
        self.socio.save()
        self.assertFalse(self.socio.membresia_vigente())
    
    def test_clase_cupos_disponibles(self):
        """Test RF-002: Cálculo de cupos disponibles"""
        self.assertEqual(self.clase.get_cupos_disponibles(), 10)
        
        # Crear reserva
        Reserva.objects.create(
            socio=self.user,
            clase=self.clase,
            socio_perfil=self.socio
        )
        
        self.assertEqual(self.clase.get_cupos_disponibles(), 9)
    
    def test_clase_esta_llena(self):
        """Test RF-003: Detección de clase llena"""
        self.assertFalse(self.clase.esta_llena)
        
        # Llenar la clase
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                password='pass123'
            )
            socio = Socio.objects.create(
                user=user,
                rut=f'1234567{i}-9',
                numero_socio=f'SOC00{i}',
                fecha_inicio_membresia=date.today() - timedelta(days=30),
                fecha_fin_membresia=date.today() + timedelta(days=30),
                estado_membresia='activa'
            )
            Reserva.objects.create(
                socio=user,
                clase=self.clase,
                socio_perfil=socio
            )