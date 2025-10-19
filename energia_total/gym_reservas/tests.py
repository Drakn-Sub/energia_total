from django.test import TestCase
from django.urls import reverse
from .models import Clase, Reserva
from django.contrib.auth.models import User

class ClaseModelTest(TestCase):
    def setUp(self):
        self.clase = Clase.objects.create(nombre="Yoga", descripcion="Clase de yoga para principiantes", capacidad=10)

    def test_clase_creation(self):
        self.assertEqual(self.clase.nombre, "Yoga")
        self.assertEqual(self.clase.descripcion, "Clase de yoga para principiantes")
        self.assertEqual(self.clase.capacidad, 10)

class ReservaModelTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='testuser', password='12345')
        self.clase = Clase.objects.create(nombre="Pilates", descripcion="Clase de pilates", capacidad=5)
        self.reserva = Reserva.objects.create(usuario=self.usuario, clase=self.clase)

    def test_reserva_creation(self):
        self.assertEqual(self.reserva.usuario.username, 'testuser')
        self.assertEqual(self.reserva.clase.nombre, "Pilates")

class ClaseViewTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='testuser', password='12345')
        self.clase = Clase.objects.create(nombre="Zumba", descripcion="Clase de zumba", capacidad=15)

    def test_clase_list_view(self):
        response = self.client.get(reverse('gym_reservas:clase_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Zumba")

    def test_clase_detail_view(self):
        response = self.client.get(reverse('gym_reservas:clase_detail', args=[self.clase.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Clase de zumba")

class ReservaViewTest(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username='testuser', password='12345')
        self.client.login(username='testuser', password='12345')
        self.clase = Clase.objects.create(nombre="Boxeo", descripcion="Clase de boxeo", capacidad=10)

    def test_reserva_create_view(self):
        response = self.client.post(reverse('gym_reservas:reserva_create', args=[self.clase.id]))
        self.assertEqual(response.status_code, 302)  # Redirección después de crear la reserva

    def test_reserva_cancel_view(self):
        reserva = Reserva.objects.create(usuario=self.usuario, clase=self.clase)
        response = self.client.post(reverse('gym_reservas:reserva_cancel', args=[reserva.id]))
        self.assertEqual(response.status_code, 302)  # Redirección después de cancelar la reserva