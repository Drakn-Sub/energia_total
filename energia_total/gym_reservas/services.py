"""
Capa de servicios con patrones de diseño:
- Strategy Pattern: Para validación de reservas
- Repository Pattern: Para acceso a datos
"""

from abc import ABC, abstractmethod
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Clase, Reserva, ListaEspera, Asistencia


# ============================================================================
# PATRÓN STRATEGY: Estrategias de Validación de Reservas
# ============================================================================

class ReservaValidationStrategy(ABC):
    """Interfaz para estrategias de validación"""
    
    @abstractmethod
    def validate(self, socio, clase) -> tuple[bool, str]:
        """
        Valida si se puede realizar la reserva
        Returns: (es_valido, mensaje_error)
        """
        pass


class MembresiaValidationStrategy(ReservaValidationStrategy):
    """Validación de membresía vigente"""
    
    def validate(self, socio, clase) -> tuple[bool, str]:
        try:
            socio_perfil = socio.socio
            if not socio_perfil.membresia_vigente():
                return False, "Tu membresía no está vigente"
        except Exception:
            return False, "No tienes un perfil de socio asociado"
        return True, ""


class CuposDisponiblesStrategy(ReservaValidationStrategy):
    """Validación de cupos disponibles (anti-sobrecupo)"""
    
    def validate(self, socio, clase) -> tuple[bool, str]:
        if clase.get_cupos_disponibles() <= 0:
            return False, "No hay cupos disponibles"
        return True, ""


class LimiteReservasStrategy(ReservaValidationStrategy):
    """Validación de límite de 3 reservas activas (RF-003)"""
    
    def validate(self, socio, clase) -> tuple[bool, str]:
        reservas_activas = Reserva.objects.filter(
            socio=socio,
            estado='confirmada',
            clase__fecha__gte=timezone.now().date()
        ).count()
        
        if reservas_activas >= 3:
            return False, "Has alcanzado el límite de 3 reservas activas"
        return True, ""


class ReservaDuplicadaStrategy(ReservaValidationStrategy):
    """Validación de reserva duplicada"""
    
    def validate(self, socio, clase) -> tuple[bool, str]:
        existe = Reserva.objects.filter(
            socio=socio,
            clase=clase,
            estado='confirmada'
        ).exists()
        
        if existe:
            return False, "Ya tienes una reserva para esta clase"
        return True, ""


class ClaseDisponibleStrategy(ReservaValidationStrategy):
    """Validación de disponibilidad de la clase"""
    
    def validate(self, socio, clase) -> tuple[bool, str]:
        if not clase.puede_reservarse():
            return False, "Esta clase no está disponible para reservas"
        return True, ""


class ReservaValidator:
    """
    Contexto que ejecuta las estrategias de validación
    Implementa el patrón Strategy
    """
    
    def __init__(self):
        self.strategies = [
            ClaseDisponibleStrategy(),
            MembresiaValidationStrategy(),
            CuposDisponiblesStrategy(),
            LimiteReservasStrategy(),
            ReservaDuplicadaStrategy(),
        ]
    
    def validate_all(self, socio, clase) -> tuple[bool, list[str]]:
        """
        Ejecuta todas las estrategias de validación
        Returns: (todas_validas, lista_errores)
        """
        errores = []
        
        for strategy in self.strategies:
            es_valido, mensaje = strategy.validate(socio, clase)
            if not es_valido:
                errores.append(mensaje)
        
        return len(errores) == 0, errores


# ============================================================================
# PATRÓN REPOSITORY: Acceso a Datos Centralizado
# ============================================================================

class ClaseRepository:
    """Repository para operaciones sobre Clase"""
    
    @staticmethod
    def get_clases_disponibles(filtros=None):
        """Obtiene clases disponibles con filtros opcionales"""
        queryset = Clase.objects.filter(
            fecha__gte=timezone.now().date(),
            estado='programada'
        ).select_related('instructor__user', 'sala')
        
        if filtros:
            if 'tipo' in filtros:
                queryset = queryset.filter(tipo=filtros['tipo'])
            if 'fecha' in filtros:
                queryset = queryset.filter(fecha=filtros['fecha'])
            if 'instructor_id' in filtros:
                queryset = queryset.filter(instructor_id=filtros['instructor_id'])
        
        return queryset.order_by('fecha', 'hora_inicio')
    
    @staticmethod
    def get_clase_con_disponibilidad(clase_id):
        """Obtiene clase con información de disponibilidad"""
        try:
            clase = Clase.objects.select_related(
                'instructor__user', 'sala'
            ).get(pk=clase_id)
            return clase
        except Clase.DoesNotExist:
            return None
    
    @staticmethod
    def verificar_conflicto_horario(sala, fecha, hora_inicio, hora_fin, excluir_clase_id=None):
        """Verifica conflictos de horario en una sala"""
        queryset = Clase.objects.filter(
            sala=sala,
            fecha=fecha,
            estado='programada'
        )
        
        if excluir_clase_id:
            queryset = queryset.exclude(pk=excluir_clase_id)
        
        for clase in queryset:
            otra_hora_fin = clase.get_hora_fin()
            # Verificar solapamiento
            if not (hora_inicio >= otra_hora_fin or hora_fin <= clase.hora_inicio):
                return True, clase
        
        return False, None


class ReservaRepository:
    """Repository para operaciones sobre Reserva"""
    
    @staticmethod
    def get_reservas_activas_socio(socio):
        """Obtiene reservas activas de un socio"""
        return Reserva.objects.filter(
            socio=socio,
            estado='confirmada',
            clase__fecha__gte=timezone.now().date()
        ).select_related('clase').order_by('clase__fecha', 'clase__hora_inicio')
    
    @staticmethod
    def get_reserva_by_id(reserva_id, socio=None):
        """Obtiene una reserva específica"""
        try:
            queryset = Reserva.objects.select_related('clase', 'socio')
            if socio:
                queryset = queryset.filter(socio=socio)
            return queryset.get(pk=reserva_id)
        except Reserva.DoesNotExist:
            return None
    
    @staticmethod
    def contar_no_shows_socio(socio, ultimos_dias=30):
        """Cuenta los no-shows de un socio en los últimos N días"""
        fecha_limite = timezone.now().date() - timedelta(days=ultimos_dias)
        return Asistencia.objects.filter(
            reserva__socio=socio,
            reserva__clase__fecha__gte=fecha_limite,
            asistio=False
        ).count()


# ============================================================================
# SERVICIOS DE NEGOCIO
# ============================================================================

class ReservaService:
    """
    Servicio principal para gestión de reservas
    Implementa lógica de negocio con transacciones ACID
    """
    
    def __init__(self):
        self.validator = ReservaValidator()
        self.reserva_repo = ReservaRepository()
        self.clase_repo = ClaseRepository()
    
    @transaction.atomic
    def crear_reserva(self, socio, clase_id):
        """
        Crea una reserva con validaciones transaccionales
        RF-003: Reservar Clase con validación de cupos
        """
        # 1. Obtener clase con lock para evitar condiciones de carrera
        try:
            clase = Clase.objects.select_for_update().get(pk=clase_id)
        except Clase.DoesNotExist:
            return False, "Clase no encontrada"
        
        # 2. Validar con estrategias
        es_valido, errores = self.validator.validate_all(socio, clase)
        if not es_valido:
            return False, " | ".join(errores)
        
        # 3. Verificar cupos nuevamente (doble verificación transaccional)
        if clase.get_cupos_disponibles() <= 0:
            return False, "No hay cupos disponibles (verificación transaccional)"
        
        # 4. Crear reserva
        try:
            reserva = Reserva.objects.create(
                socio=socio,
                clase=clase,
                estado='confirmada',
                socio_perfil=socio.socio if hasattr(socio, 'socio') else None
            )
            return True, reserva
        except Exception as e:
            return False, f"Error al crear reserva: {str(e)}"
    
    @transaction.atomic
    def cancelar_reserva(self, reserva_id, socio):
        """
        Cancela una reserva con validación de tiempo
        RF-004: Cancelación hasta 2 horas antes
        """
        reserva = self.reserva_repo.get_reserva_by_id(reserva_id, socio)
        
        if not reserva:
            return False, "Reserva no encontrada"
        
        if reserva.estado != 'confirmada':
            return False, "Esta reserva no puede cancelarse"
        
        if not reserva.puede_cancelarse():
            return False, "No puedes cancelar con menos de 2 horas de anticipación"
        
        # Cancelar reserva
        reserva.estado = 'cancelada'
        reserva.fecha_cancelacion = timezone.now()
        reserva.save()
        
        # Procesar lista de espera si existe
        self._procesar_lista_espera(reserva.clase)
        
        return True, "Reserva cancelada exitosamente"
    
    def _procesar_lista_espera(self, clase):
        """
        Algoritmo de prioridad para lista de espera
        Procesa automáticamente cuando se libera un cupo
        """
        if clase.get_cupos_disponibles() <= 0:
            return
        
        # Obtener siguiente en lista ordenada por prioridad
        siguiente = ListaEspera.objects.filter(
            clase=clase,
            notificado=False
        ).order_by('-prioridad', 'fecha_registro').first()
        
        if siguiente:
            # Crear reserva automática
            try:
                Reserva.objects.create(
                    socio=siguiente.socio,
                    clase=clase,
                    estado='confirmada',
                    prioridad=siguiente.prioridad
                )
                siguiente.notificado = True
                siguiente.save()
                
                # TODO: Enviar notificación por email
                
            except Exception as e:
                pass  # Log error pero no fallar


class CuposService:
    """
    Servicio para consulta de disponibilidad en tiempo real
    RF-002: Búsqueda con disponibilidad actualizada
    """
    
    def __init__(self):
        self.clase_repo = ClaseRepository()
    
    def get_disponibilidad_clase(self, clase_id):
        """Obtiene disponibilidad de una clase específica"""
        clase = self.clase_repo.get_clase_con_disponibilidad(clase_id)
        
        if not clase:
            return None
        
        return {
            'clase_id': clase.id,
            'nombre': clase.nombre,
            'capacidad_total': clase.capacidad,
            'cupos_disponibles': clase.get_cupos_disponibles(),
            'esta_llena': clase.esta_llena,
            'puede_reservarse': clase.puede_reservarse(),
            'fecha': clase.fecha,
            'hora_inicio': clase.hora_inicio,
        }
    
    def get_disponibilidad_multiple(self, filtros=None):
        """
        Obtiene disponibilidad de múltiples clases
        Optimizado para carga rápida (< 3 segundos según RNF-003)
        """
        clases = self.clase_repo.get_clases_disponibles(filtros)
        
        resultado = []
        for clase in clases:
            resultado.append({
                'clase_id': clase.id,
                'nombre': clase.nombre,
                'tipo': clase.get_tipo_display(),
                'fecha': clase.fecha,
                'hora_inicio': clase.hora_inicio,
                'instructor': clase.instructor.user.get_full_name() if clase.instructor else clase.instructor_nombre,
                'cupos_disponibles': clase.get_cupos_disponibles(),
                'capacidad_total': clase.capacidad,
                'precio': float(clase.precio),
                'esta_llena': clase.esta_llena,
            })
        
        return resultado


class ReporteService:
    """Servicio para generación de reportes"""
    
    @staticmethod
    def generar_reporte_no_shows(fecha_inicio, fecha_fin):
        """Genera reporte de no-shows en un período"""
        asistencias = Asistencia.objects.filter(
            asistio=False,
            reserva__clase__fecha__range=[fecha_inicio, fecha_fin]
        ).select_related('reserva__socio', 'reserva__clase')
        
        reporte = []
        for asistencia in asistencias:
            reporte.append({
                'socio_id': asistencia.reserva.socio.id,
                'socio_nombre': asistencia.reserva.socio.get_full_name(),
                'clase_id': asistencia.reserva.clase.id,
                'clase_nombre': asistencia.reserva.clase.nombre,
                'fecha': asistencia.reserva.clase.fecha,
                'hora_inicio': asistencia.reserva.clase.hora_inicio,
            })
        
        return reporte
    
    @staticmethod
    def generar_reporte_asistencia(fecha_inicio, fecha_fin):
        """Genera reporte de asistencia por clase"""
        from django.db.models import Count, Q
        
        clases = Clase.objects.filter(
            fecha__range=[fecha_inicio, fecha_fin]
        ).annotate(
            total_reservas=Count('reserva', filter=Q(reserva__estado='confirmada')),
            total_asistencias=Count('reserva__asistencia', filter=Q(reserva__asistencia__asistio=True)),
            total_no_shows=Count('reserva__asistencia', filter=Q(reserva__asistencia__asistio=False))
        )
        
        reporte = []
        for clase in clases:
            porcentaje = (clase.total_asistencias / clase.total_reservas * 100) if clase.total_reservas > 0 else 0
            reporte.append({
                'clase_id': clase.id,
                'clase_nombre': clase.nombre,
                'fecha': clase.fecha,
                'total_reservas': clase.total_reservas,
                'total_asistencias': clase.total_asistencias,
                'porcentaje_asistencia': round(porcentaje, 2),
                'total_no_shows': clase.total_no_shows,
            })
        
        return reporte


class ListaEsperaService:
    """Servicio para gestión de lista de espera"""
    
    @transaction.atomic
    def agregar_a_lista_espera(self, socio, clase_id):
        """Agrega un socio a la lista de espera"""
        try:
            clase = Clase.objects.get(pk=clase_id)
        except Clase.DoesNotExist:
            return False, "Clase no encontrada"
        
        # Verificar que la clase esté llena
        if not clase.esta_llena:
            return False, "La clase tiene cupos disponibles"
        
        # Verificar duplicado
        existe = ListaEspera.objects.filter(
            socio=socio,
            clase=clase
        ).exists()
        
        if existe:
            return False, "Ya estás en la lista de espera"
        
        # Calcular prioridad
        dias_socio = (timezone.now().date() - socio.date_joined.date()).days
        reservas_previas = Reserva.objects.filter(
            socio=socio,
            estado='confirmada'
        ).count()
        prioridad = dias_socio + (reservas_previas * 10)
        
        # Crear entrada
        lista = ListaEspera.objects.create(
            socio=socio,
            clase=clase,
            prioridad=prioridad
        )
        
        return True, lista