from django.db import models
from django.contrib.auth.models import User

class Clase(models.Model):
    TIPOS_CLASE = [
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('spinning', 'Spinning'),
        ('crossfit', 'CrossFit'),
        ('zumba', 'Zumba'),
        ('boxing', 'Boxing'),
        ('musculacion', 'Musculación'),
    ]
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_CLASE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    duracion = models.DurationField()
    capacidad = models.PositiveIntegerField()
    instructor = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    #cliente
    
    def __str__(self):
        return f'{self.nombre} - {self.get_tipo_display()}'
    
    @property
    def esta_llena(self):
        return self.reserva_set.filter(estado='confirmada').count() >= self.capacidad

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]
    
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    socio = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='confirmada')

    def __str__(self):
        return f'Reserva de {self.socio.username} para {self.clase.nombre}'