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
            Reserva.objects.create(
                socio=user,
                clase=self.clase
            )
        
        self.assertTrue(self.clase.esta_llena)
    
    def test_reserva_puede_cancelarse(self):
        """Test RF-004: Cancelación hasta 2 horas antes"""
        reserva = Reserva.objects.create(
            socio=self.user,
            clase=self.clase,
            socio_perfil=self.socio
        )
        
        # Clase en 1 día, debería poder cancelarse
        self.assertTrue(reserva.puede_cancelarse())
        
        # Cambiar clase a 1 hora antes
        self.clase.fecha = date.today()
        self.clase.hora_inicio = (timezone.now() + timedelta(hours=1)).time()
        self.clase.save()
        
        # Refrescar reserva
        reserva.refresh_from_db()
        
        # No debería poder cancelarse (menos de 2 horas)
        self.assertFalse(reserva.puede_cancelarse())


class ServiciosTestCase(TestCase):
    """Tests de servicios con patrones de diseño"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.socio = Socio.objects.create(
            user=self.user,
            rut='12345678-9',
            numero_socio='SOC001',
            fecha_inicio_membresia=date.today() - timedelta(days=30),
            fecha_fin_membresia=date.today() + timedelta(days=30),
            estado_membresia='activa'
        )
        
        instructor_user = User.objects.create_user(username='instructor', password='pass')
        self.instructor = Instructor.objects.create(
            user=instructor_user,
            especialidades='Yoga',
            fecha_contratacion=date.today()
        )
        
        self.sala = Sala.objects.create(
            nombre='Sala Test',
            capacidad_maxima=10,
            tipo_sala='yoga'
        )
        
        self.clase = Clase.objects.create(
            nombre='Yoga Test',
            descripcion='Test',
            tipo='yoga',
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(10, 0),
            duracion=timedelta(hours=1),
            capacidad=5,
            instructor=self.instructor,
            instructor_nombre='Test Instructor',
            sala=self.sala,
            precio=Decimal('25000')
        )
    
    def test_patron_strategy_validacion(self):
        """Test del patrón Strategy en validaciones"""
        validator = ReservaValidator()
        
        # Validación exitosa
        es_valido, errores = validator.validate_all(self.user, self.clase)
        self.assertTrue(es_valido)
        self.assertEqual(len(errores), 0)
    
    def test_patron_strategy_membresia_vencida(self):
        """Test Strategy: Rechaza membresía vencida"""
        # Vencer membresía
        self.socio.fecha_fin_membresia = date.today() - timedelta(days=1)
        self.socio.save()
        
        validator = ReservaValidator()
        es_valido, errores = validator.validate_all(self.user, self.clase)
        
        self.assertFalse(es_valido)
        self.assertTrue(any('membresía' in error.lower() for error in errores))
    
    def test_servicio_crear_reserva_exitosa(self):
        """Test RF-003: Creación exitosa de reserva"""
        servicio = ReservaService()
        
        exito, resultado = servicio.crear_reserva(self.user, self.clase.id)
        
        self.assertTrue(exito)
        self.assertIsInstance(resultado, Reserva)
        self.assertEqual(resultado.socio, self.user)
        self.assertEqual(resultado.clase, self.clase)
    
    def test_servicio_prevenir_sobrecupo(self):
        """Test RF-003: Sistema anti-sobrecupo"""
        servicio = ReservaService()
        
        # Llenar la clase
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                password='pass'
            )
            Socio.objects.create(
                user=user,
                rut=f'1234567{i}-9',
                numero_socio=f'SOC00{i}',
                fecha_inicio_membresia=date.today(),
                fecha_fin_membresia=date.today() + timedelta(days=30),
                estado_membresia='activa'
            )
            servicio.crear_reserva(user, self.clase.id)
        
        # Intentar reservar en clase llena
        new_user = User.objects.create_user(username='overflow', password='pass')
        Socio.objects.create(
            user=new_user,
            rut='99999999-9',
            numero_socio='SOC999',
            fecha_inicio_membresia=date.today(),
            fecha_fin_membresia=date.today() + timedelta(days=30),
            estado_membresia='activa'
        )
        
        exito, mensaje = servicio.crear_reserva(new_user, self.clase.id)
        
        self.assertFalse(exito)
        self.assertIn('cupo', mensaje.lower())
    
    def test_servicio_limite_3_reservas(self):
        """Test RF-003: Límite de 3 reservas activas"""
        servicio = ReservaService()
        
        # Crear 3 clases
        clases = []
        for i in range(4):
            clase = Clase.objects.create(
                nombre=f'Clase {i}',
                descripcion='Test',
                tipo='yoga',
                fecha=date.today() + timedelta(days=i+1),
                hora_inicio=time(10, 0),
                duracion=timedelta(hours=1),
                capacidad=10,
                instructor=self.instructor,
                instructor_nombre='Test',
                sala=self.sala,
                precio=Decimal('25000')
            )
            clases.append(clase)
        
        # Reservar 3 clases (OK)
        for i in range(3):
            exito, _ = servicio.crear_reserva(self.user, clases[i].id)
            self.assertTrue(exito)
        
        # Intentar 4ta reserva (FALLA)
        exito, mensaje = servicio.crear_reserva(self.user, clases[3].id)
        self.assertFalse(exito)
        self.assertIn('límite', mensaje.lower())
    
    def test_servicio_cancelar_reserva(self):
        """Test RF-004: Cancelación de reserva"""
        servicio = ReservaService()
        
        # Crear reserva
        exito, reserva = servicio.crear_reserva(self.user, self.clase.id)
        self.assertTrue(exito)
        
        # Cancelar
        exito, mensaje = servicio.cancelar_reserva(reserva.id, self.user)
        self.assertTrue(exito)
        
        # Verificar estado
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')
    
    def test_servicio_cancelar_con_menos_2_horas(self):
        """Test RF-004: No permite cancelar con menos de 2 horas"""
        # Clase en 1 hora
        self.clase.fecha = date.today()
        self.clase.hora_inicio = (timezone.now() + timedelta(hours=1)).time()
        self.clase.save()
        
        servicio = ReservaService()
        
        # Crear reserva
        exito, reserva = servicio.crear_reserva(self.user, self.clase.id)
        self.assertTrue(exito)
        
        # Intentar cancelar
        exito, mensaje = servicio.cancelar_reserva(reserva.id, self.user)
        self.assertFalse(exito)
        self.assertIn('2 horas', mensaje.lower())
    
    def test_cupos_service_disponibilidad(self):
        """Test RF-002: Consulta de disponibilidad en tiempo real"""
        servicio = CuposService()
        
        disponibilidad = servicio.get_disponibilidad_clase(self.clase.id)
        
        self.assertIsNotNone(disponibilidad)
        self.assertEqual(disponibilidad['cupos_disponibles'], 5)
        self.assertFalse(disponibilidad['esta_llena'])
        self.assertTrue(disponibilidad['puede_reservarse'])
    
    def test_algoritmo_prioridad_lista_espera(self):
        """Test del algoritmo de prioridad"""
        # Usuario antiguo con muchas reservas
        user_antiguo = User.objects.create_user(
            username='antiguo',
            password='pass',
            date_joined=timezone.now() - timedelta(days=365)
        )
        
        # Usuario nuevo sin reservas
        user_nuevo = User.objects.create_user(
            username='nuevo',
            password='pass',
            date_joined=timezone.now()
        )
        
        # Simular reservas previas del antiguo
        for i in range(10):
            clase_previa = Clase.objects.create(
                nombre=f'Clase Previa {i}',
                descripcion='Test',
                tipo='yoga',
                fecha=date.today() - timedelta(days=i+1),
                hora_inicio=time(10, 0),
                duracion=timedelta(hours=1),
                capacidad=10,
                instructor=self.instructor,
                instructor_nombre='Test',
                sala=self.sala,
                precio=Decimal('25000'),
                estado='finalizada'
            )
            Reserva.objects.create(
                socio=user_antiguo,
                clase=clase_previa,
                estado='confirmada'
            )
        
        # Crear reserva para calcular prioridad
        reserva_antiguo = Reserva(socio=user_antiguo, clase=self.clase)
        reserva_antiguo.save()
        
        reserva_nuevo = Reserva(socio=user_nuevo, clase=self.clase)
        reserva_nuevo.save()
        
        # El usuario antiguo debe tener mayor prioridad
        self.assertGreater(reserva_antiguo.prioridad, reserva_nuevo.prioridad)


class VistasTestCase(TestCase):
    """Tests de vistas y flujo completo"""
    
    def setUp(self):
        self.client = Client()
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.socio = Socio.objects.create(
            user=self.user,
            rut='12345678-9',
            numero_socio='SOC001',
            fecha_inicio_membresia=date.today() - timedelta(days=30),
            fecha_fin_membresia=date.today() + timedelta(days=30),
            estado_membresia='activa'
        )
        
        instructor_user = User.objects.create_user(username='instructor', password='pass')
        self.instructor = Instructor.objects.create(
            user=instructor_user,
            especialidades='Yoga',
            fecha_contratacion=date.today()
        )
        
        self.sala = Sala.objects.create(
            nombre='Sala Test',
            capacidad_maxima=10,
            tipo_sala='yoga'
        )
        
        self.clase = Clase.objects.create(
            nombre='Yoga Test',
            descripcion='Test',
            tipo='yoga',
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(10, 0),
            duracion=timedelta(hours=1),
            capacidad=10,
            instructor=self.instructor,
            instructor_nombre='Test',
            sala=self.sala,
            precio=Decimal('25000')
        )
    
    def test_index_view(self):
        """Test de página principal"""
        response = self.client.get('/gym/')
        self.assertEqual(response.status_code, 200)
    
    def test_lista_clases_view(self):
        """Test RF-002: Vista de lista de clases"""
        response = self.client.get('/gym/clases/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yoga Test')
    
    def test_lista_clases_filtro_tipo(self):
        """Test RF-002: Filtrado por tipo"""
        response = self.client.get('/gym/clases/?tipo=yoga')
        self.assertEqual(response.status_code, 200)
    
    def test_detalle_clase_sin_login(self):
        """Test que usuario no autenticado puede ver clase"""
        response = self.client.get(f'/gym/clases/{self.clase.id}/')
        self.assertEqual(response.status_code, 200)
    
    def test_reservar_requiere_login(self):
        """Test RF-003: Reservar requiere autenticación"""
        response = self.client.post(
            f'/gym/clases/{self.clase.id}/',
            {'reservar': 'true'}
        )
        # Debe redirigir a login
        self.assertEqual(response.status_code, 302)
    
    def test_flujo_completo_reserva(self):
        """Test del flujo completo de reserva"""
        # Login
        self.client.login(username='testuser', password='testpass123')
        
        # Hacer reserva
        response = self.client.post(
            f'/gym/clases/{self.clase.id}/',
            {'reservar': 'true'}
        )
        
        # Debe redirigir
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó la reserva
        self.assertTrue(
            Reserva.objects.filter(
                socio=self.user,
                clase=self.clase,
                estado='confirmada'
            ).exists()
        )
    
    def test_mis_reservas_requiere_login(self):
        """Test que mis reservas requiere autenticación"""
        response = self.client.get('/gym/mis-reservas/')
        self.assertEqual(response.status_code, 302)  # Redirect a login
    
    def test_login_view(self):
        """Test RF-001: Vista de login"""
        response = self.client.get('/gym/login/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_exitoso(self):
        """Test RF-001: Login con credenciales correctas"""
        response = self.client.post('/gym/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect después de login


class SeguridadTestCase(TestCase):
    """Tests de seguridad (RNF-001)"""
    
    def test_password_hasheado_bcrypt(self):
        """Test que las contraseñas se hashean con bcrypt"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # La contraseña no debe estar en texto plano
        self.assertNotEqual(user.password, 'testpass123')
        
        # Debe empezar con identificador de bcrypt
        self.assertTrue(user.password.startswith('bcrypt'))
    
    def test_csrf_protection(self):
        """Test que POST sin CSRF token falla"""
        client = Client(enforce_csrf_checks=True)
        
        response = client.post('/gym/login/', {
            'username': 'test',
            'password': 'pass'
        })
        
        # Debe fallar por falta de CSRF token
        self.assertEqual(response.status_code, 403)


class RendimientoTestCase(TestCase):
    """Tests de rendimiento (RNF-003)"""
    
    def test_query_optimizado_lista_clases(self):
        """Test que lista de clases usa select_related"""
        import time
        
        # Crear datos
        instructor_user = User.objects.create_user(username='instructor', password='pass')
        instructor = Instructor.objects.create(
            user=instructor_user,
            especialidades='Yoga',
            fecha_contratacion=date.today()
        )
        
        sala = Sala.objects.create(
            nombre='Sala',
            capacidad_maxima=10,
            tipo_sala='yoga'
        )
        
        # Crear 50 clases
        for i in range(50):
            Clase.objects.create(
                nombre=f'Clase {i}',
                descripcion='Test',
                tipo='yoga',
                fecha=date.today() + timedelta(days=i),
                hora_inicio=time(10, 0),
                duracion=timedelta(hours=1),
                capacidad=10,
                instructor=instructor,
                instructor_nombre='Test',
                sala=sala,
                precio=Decimal('25000')
            )
        
        # Medir tiempo de consulta
        from django.db import connection
        from django.test.utils import override_settings
        
        with override_settings(DEBUG=True):
            connection.queries_log.clear()
            
            start = time.time()
            list(Clase.objects.all().select_related('instructor__user', 'sala'))
            elapsed = time.time() - start
            
            # Debe completar en menos de 1 segundo
            self.assertLess(elapsed, 1.0)
            
            # Debe usar pocas queries (select_related)
            self.assertLess(len(connection.queries), 5)


class IntegracionTestCase(TestCase):
    """Tests de integración end-to-end"""
    
    def test_escenario_completo_socio(self):
        """Test del escenario completo de un socio"""
        # 1. Crear usuario y socio
        user = User.objects.create_user(
            username='socio1',
            password='pass123'
        )
        
        socio = Socio.objects.create(
            user=user,
            rut='12345678-9',
            numero_socio='SOC001',
            fecha_inicio_membresia=date.today(),
            fecha_fin_membresia=date.today() + timedelta(days=30),
            estado_membresia='activa'
        )
        
        # 2. Crear clase
        instructor_user = User.objects.create_user(username='inst', password='pass')
        instructor = Instructor.objects.create(
            user=instructor_user,
            especialidades='Yoga',
            fecha_contratacion=date.today()
        )
        
        sala = Sala.objects.create(nombre='Sala', capacidad_maxima=10, tipo_sala='yoga')
        
        clase = Clase.objects.create(
            nombre='Yoga Matutino',
            descripcion='Test',
            tipo='yoga',
            fecha=date.today() + timedelta(days=1),
            hora_inicio=time(8, 0),
            duracion=timedelta(hours=1),
            capacidad=10,
            instructor=instructor,
            instructor_nombre='Instructor Test',
            sala=sala,
            precio=Decimal('25000')
        )
        
        # 3. Consultar disponibilidad
        servicio_cupos = CuposService()
        disp = servicio_cupos.get_disponibilidad_clase(clase.id)
        self.assertEqual(disp['cupos_disponibles'], 10)
        
        # 4. Hacer reserva
        servicio_reserva = ReservaService()
        exito, reserva = servicio_reserva.crear_reserva(user, clase.id)
        self.assertTrue(exito)
        
        # 5. Verificar cupos actualizados
        disp = servicio_cupos.get_disponibilidad_clase(clase.id)
        self.assertEqual(disp['cupos_disponibles'], 9)
        
        # 6. Cancelar reserva
        exito, msg = servicio_reserva.cancelar_reserva(reserva.id, user)
        self.assertTrue(exito)
        
        # 7. Verificar cupos restaurados
        disp = servicio_cupos.get_disponibilidad_clase(clase.id)
        self.assertEqual(disp['cupos_disponibles'], 10)