from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

class Socio(models.Model):
    """Perfil extendido del socio con información de membresía"""
    ESTADO_MEMBRESIA = [
        ('activa', 'Activa'),
        ('vencida', 'Vencida'),
        ('suspendida', 'Suspendida'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='socio')
    rut = models.CharField(max_length=12, unique=True, help_text='Formato: 12345678-9')
    numero_socio = models.CharField(max_length=10, unique=True)
    fecha_inicio_membresia = models.DateField()
    fecha_fin_membresia = models.DateField()
    estado_membresia = models.CharField(max_length=20, choices=ESTADO_MEMBRESIA, default='activa')
    telefono = models.CharField(max_length=15, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Socio'
        verbose_name_plural = 'Socios'
        ordering = ['-fecha_registro']
    
    def __str__(self):
        return f'{self.user.get_full_name()} - {self.numero_socio}'
    
    def membresia_vigente(self):
        """Verifica si la membresía está vigente"""
        return (self.estado_membresia == 'activa' and 
                self.fecha_fin_membresia >= timezone.now().date())
    
    def clean(self):
        """Validación del formato RUT chileno"""
        if self.rut:
            # Validación básica del formato RUT
            import re
            if not re.match(r'^\d{7,8}-[\dkK]$', self.rut):
                raise ValidationError('Formato de RUT inválido. Use: 12345678-9')


class Instructor(models.Model):
    """Perfil de instructor"""
    ESTADO_INSTRUCTOR = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor')
    especialidades = models.CharField(max_length=200, help_text='Separar por comas')
    certificaciones = models.TextField(blank=True)
    fecha_contratacion = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_INSTRUCTOR, default='activo')
    
    class Meta:
        verbose_name = 'Instructor'
        verbose_name_plural = 'Instructores'
    
    def __str__(self):
        return self.user.get_full_name()


class TipoClase(models.Model):
    """Catálogo de tipos de clases"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    duracion_minutos = models.PositiveIntegerField(default=60)
    cupo_maximo_default = models.PositiveIntegerField(default=20)
    requiere_instructor = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Tipo de Clase'
        verbose_name_plural = 'Tipos de Clases'
    
    def __str__(self):
        return self.nombre


class Sala(models.Model):
    """Espacios físicos del gimnasio"""
    TIPO_SALA = [
        ('yoga', 'Yoga'),
        ('cardio', 'Cardio'),
        ('musculacion', 'Musculación'),
        ('funcional', 'Funcional'),
        ('spinning', 'Spinning'),
    ]
    
    ESTADO_SALA = [
        ('disponible', 'Disponible'),
        ('mantenimiento', 'En Mantenimiento'),
        ('ocupada', 'Ocupada'),
    ]
    
    nombre = models.CharField(max_length=100)
    capacidad_maxima = models.PositiveIntegerField()
    tipo_sala = models.CharField(max_length=20, choices=TIPO_SALA)
    equipamiento = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_SALA, default='disponible')
    
    class Meta:
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'
    
    def __str__(self):
        return f'{self.nombre} ({self.get_tipo_sala_display()})'


class Clase(models.Model):
    """Clase programada con validaciones de negocio"""
    TIPOS_CLASE = [
        ('yoga', 'Yoga'),
        ('pilates', 'Pilates'),
        ('spinning', 'Spinning'),
        ('crossfit', 'CrossFit'),
        ('zumba', 'Zumba'),
        ('boxing', 'Boxing'),
        ('musculacion', 'Musculación'),
    ]
    
    ESTADO_CLASE = [
        ('programada', 'Programada'),
        ('en_curso', 'En Curso'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]
    
    tipo_clase = models.ForeignKey(TipoClase, on_delete=models.PROTECT, null=True, blank=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_CLASE)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    duracion = models.DurationField(default=timedelta(hours=1))
    capacidad = models.PositiveIntegerField()
    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='clases_asignadas'
    )
    instructor_nombre = models.CharField(max_length=100)  # Mantener compatibilidad
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADO_CLASE, default='programada')
    
    class Meta:
        verbose_name = 'Clase'
        verbose_name_plural = 'Clases'
        ordering = ['fecha', 'hora_inicio']
        indexes = [
            models.Index(fields=['fecha', 'hora_inicio']),
            models.Index(fields=['tipo']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(capacidad__gt=0),
                name='capacidad_positiva'
            )
        ]
    
    def __str__(self):
        return f'{self.nombre} - {self.get_tipo_display()} ({self.fecha} {self.hora_inicio})'
    
    @property
    def esta_llena(self):
        """Verifica si la clase alcanzó su capacidad máxima"""
        return self.get_cupos_disponibles() <= 0
    
    def get_cupos_disponibles(self):
        """Calcula cupos disponibles en tiempo real"""
        reservas_confirmadas = self.reserva_set.filter(estado='confirmada').count()
        return max(0, self.capacidad - reservas_confirmadas)
    
    def get_hora_fin(self):
        """Calcula hora de finalización"""
        from datetime import datetime, timedelta
        inicio = datetime.combine(self.fecha, self.hora_inicio)
        fin = inicio + self.duracion
        return fin.time()
    
    def puede_reservarse(self):
        """Verifica si la clase aún puede recibir reservas"""
        ahora = timezone.now()
        clase_datetime = timezone.make_aware(
            timezone.datetime.combine(self.fecha, self.hora_inicio)
        )
        return (
            self.estado == 'programada' and
            clase_datetime > ahora and
            not self.esta_llena
        )
    
    def clean(self):
        """Validaciones de negocio"""
        # Validar que la fecha no sea pasada
        if self.fecha and self.fecha < timezone.now().date():
            raise ValidationError('No se pueden crear clases en fechas pasadas')
        
        # Validar conflictos de sala
        if self.sala and self.fecha and self.hora_inicio:
            hora_fin = self.get_hora_fin()
            conflictos = Clase.objects.filter(
                sala=self.sala,
                fecha=self.fecha,
                estado='programada'
            ).exclude(pk=self.pk)
            
            for otra_clase in conflictos:
                otra_hora_fin = otra_clase.get_hora_fin()
                # Verificar solapamiento de horarios
                if not (self.hora_inicio >= otra_hora_fin or 
                       hora_fin <= otra_clase.hora_inicio):
                    raise ValidationError(
                        f'Conflicto de horario con la clase {otra_clase.nombre} '
                        f'en la sala {self.sala.nombre}'
                    )


class Reserva(models.Model):
    """Reserva de socio con validaciones transaccionales"""
    ESTADOS_RESERVA = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('no_show', 'No Show'),
    ]
    
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    socio = models.ForeignKey(User, on_delete=models.CASCADE)
    socio_perfil = models.ForeignKey(
        Socio, 
        on_delete=models.CASCADE, 
        null=True, 
        related_name='reservas'
    )
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_RESERVA, default='confirmada')
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    prioridad = models.IntegerField(default=0)  # Para algoritmo de lista de espera
    
    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'
        ordering = ['-fecha_reserva']
        unique_together = [['socio', 'clase', 'estado']]
        indexes = [
            models.Index(fields=['socio', 'estado']),
            models.Index(fields=['clase', 'estado']),
        ]
    
    def __str__(self):
        return f'Reserva de {self.socio.username} para {self.clase.nombre}'
    
    def puede_cancelarse(self):
        """RF-004: Cancelación hasta 2 horas antes"""
        if self.estado != 'confirmada':
            return False
        
        ahora = timezone.now()
        clase_datetime = timezone.make_aware(
            timezone.datetime.combine(self.clase.fecha, self.clase.hora_inicio)
        )
        limite_cancelacion = clase_datetime - timedelta(hours=2)
        return ahora <= limite_cancelacion
    
    def clean(self):
        """Validaciones de negocio"""
        # Validar membresía vigente del socio
        if self.socio_perfil and not self.socio_perfil.membresia_vigente():
            raise ValidationError('La membresía del socio no está vigente')
        
        # Validar límite de reservas activas (RF-003: máximo 3)
        if not self.pk:  # Solo en creación
            reservas_activas = Reserva.objects.filter(
                socio=self.socio,
                estado='confirmada',
                clase__fecha__gte=timezone.now().date()
            ).count()
            
            if reservas_activas >= 3:
                raise ValidationError(
                    'Has alcanzado el límite de 3 reservas activas simultáneas'
                )
        
        # Validar que no exista reserva duplicada
        if not self.pk:
            existe = Reserva.objects.filter(
                socio=self.socio,
                clase=self.clase,
                estado='confirmada'
            ).exists()
            
            if existe:
                raise ValidationError('Ya tienes una reserva para esta clase')
    
    def save(self, *args, **kwargs):
        """Override para calcular prioridad en algoritmo de lista de espera"""
        if not self.prioridad:
            # Algoritmo de prioridad: antigüedad + historial
            dias_socio = (timezone.now().date() - 
                         self.socio.date_joined.date()).days
            reservas_previas = Reserva.objects.filter(
                socio=self.socio,
                estado='confirmada'
            ).count()
            self.prioridad = dias_socio + (reservas_previas * 10)
        
        super().save(*args, **kwargs)


class Asistencia(models.Model):
    """Registro de asistencia real"""
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    asistio = models.BooleanField(default=False)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
    
    def __str__(self):
        estado = 'Asistió' if self.asistio else 'No asistió'
        return f'{estado} - {self.reserva}'


class ListaEspera(models.Model):
    """Lista de espera para clases llenas"""
    clase = models.ForeignKey(Clase, on_delete=models.CASCADE)
    socio = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    prioridad = models.IntegerField(default=0)
    notificado = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Lista de Espera'
        verbose_name_plural = 'Listas de Espera'
        ordering = ['-prioridad', 'fecha_registro']
        unique_together = [['clase', 'socio']]
    
    def __str__(self):
        return f'{self.socio.username} en espera para {self.clase.nombre}'