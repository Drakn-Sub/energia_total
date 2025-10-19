#!/usr/bin/env python
import os
import sys
import django
from datetime import date, time, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'energia_total.settings')
django.setup()

from gym_reservas.models import Clase

# Crear clases de ejemplo
clases_ejemplo = [
    {
        'nombre': 'Yoga Matutino',
        'descripcion': 'Clase de yoga suave para empezar el día con energía positiva',
        'tipo': 'yoga',
        'fecha': date.today() + timedelta(days=1),
        'hora_inicio': time(8, 0),
        'duracion': timedelta(hours=1),
        'capacidad': 15,
        'instructor': 'Ana García',
        'precio': 25.00
    },
    {
        'nombre': 'CrossFit Intenso',
        'descripcion': 'Entrenamiento de alta intensidad para mejorar fuerza y resistencia',
        'tipo': 'crossfit',
        'fecha': date.today() + timedelta(days=1),
        'hora_inicio': time(18, 0),
        'duracion': timedelta(hours=1, minutes=30),
        'capacidad': 12,
        'instructor': 'Carlos López',
        'precio': 35.00
    },
    {
        'nombre': 'Pilates para Principiantes',
        'descripcion': 'Clase ideal para aprender los fundamentos del Pilates',
        'tipo': 'pilates',
        'fecha': date.today() + timedelta(days=2),
        'hora_inicio': time(10, 0),
        'duracion': timedelta(hours=1),
        'capacidad': 10,
        'instructor': 'María Rodríguez',
        'precio': 30.00
    },
    {
        'nombre': 'Zumba Party',
        'descripcion': '¡Diviértete bailando mientras quemas calorías!',
        'tipo': 'zumba',
        'fecha': date.today() + timedelta(days=2),
        'hora_inicio': time(19, 0),
        'duracion': timedelta(hours=1),
        'capacidad': 20,
        'instructor': 'Laura Martínez',
        'precio': 28.00
    },
    {
        'nombre': 'Spinning Cardio',
        'descripcion': 'Entrenamiento cardiovascular intenso en bicicleta estática',
        'tipo': 'spinning',
        'fecha': date.today() + timedelta(days=3),
        'hora_inicio': time(17, 30),
        'duracion': timedelta(hours=1),
        'capacidad': 16,
        'instructor': 'Pedro Sánchez',
        'precio': 32.00
    },
    {
        'nombre': 'Boxing Training',
        'descripcion': 'Aprende técnicas de boxeo y mejora tu condición física',
        'tipo': 'boxing',
        'fecha': date.today() + timedelta(days=3),
        'hora_inicio': time(20, 0),
        'duracion': timedelta(hours=1),
        'capacidad': 8,
        'instructor': 'Roberto Vega',
        'precio': 40.00
    },
    {
        'nombre': 'Musculación Básica',
        'descripcion': 'Introducción al entrenamiento con pesas y máquinas',
        'tipo': 'musculacion',
        'fecha': date.today() + timedelta(days=4),
        'hora_inicio': time(16, 0),
        'duracion': timedelta(hours=1, minutes=30),
        'capacidad': 12,
        'instructor': 'Diego Fernández',
        'precio': 35.00
    }
]

# Crear las clases
for clase_data in clases_ejemplo:
    clase = Clase.objects.create(**clase_data)
    print(f"Creada clase: {clase.nombre}")

print(f"\n¡Se crearon {len(clases_ejemplo)} clases de ejemplo!")
print("Ahora puedes acceder a http://127.0.0.1:8000/gym/ para ver las clases disponibles.")

