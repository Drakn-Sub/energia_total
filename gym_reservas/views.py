from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Clase, Reserva, Socio, ListaEspera, Asistencia
from .forms import UserRegistrationForm
from .serializers import (
    ClaseListSerializer, ClaseDetailSerializer, ReservaSerializer,
    ReporteNoShowSerializer, ReporteAsistenciaSerializer
)
from .services import (
    ReservaService, CuposService, ReporteService, ListaEsperaService
)


# ============================================================================
# VISTAS DE TEMPLATE (Para compatibilidad con templates existentes)
# ============================================================================

def index(request):
    """Vista principal de la página de inicio"""
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'gym_reservas/index.html', context)


def lista_clases(request):
    """
    Vista de listado de clases con filtros
    Utiliza CuposService para disponibilidad en tiempo real
    """
    # Filtros desde GET parameters
    filtros = {}
    tipo = request.GET.get('tipo')
    fecha = request.GET.get('fecha')
    instructor = request.GET.get('instructor')
    
    if tipo:
        filtros['tipo'] = tipo
    if fecha:
        filtros['fecha'] = fecha
    
    # Usar servicio para obtener disponibilidad
    cupos_service = CuposService()
    clases_data = cupos_service.get_disponibilidad_multiple(filtros)
    
    # Convertir a objetos Clase para el template
    clases_ids = [c['clase_id'] for c in clases_data]
    clases = Clase.objects.filter(id__in=clases_ids).order_by('fecha', 'hora_inicio')
    
    context = {
        'clases': clases,
        'tipos': Clase.TIPOS_CLASE,
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'gym_reservas/lista_clases.html', context)


def detalle_clase(request, clase_id):
    """
    Vista de detalle de clase con reserva
    Implementa RF-003 con validaciones transaccionales
    """
    clase = get_object_or_404(Clase, id=clase_id)
    reservado = False
    
    # Verificar si el usuario ya tiene reserva
    if request.user.is_authenticated:
        reservado = Reserva.objects.filter(
            socio=request.user, 
            clase=clase, 
            estado='confirmada'
        ).exists()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para hacer reservas.")
            return redirect('gym_reservas:login')
            
        reserva_service = ReservaService()
        
        if 'reservar' in request.POST:
            # Usar servicio transaccional para crear reserva
            exito, resultado = reserva_service.crear_reserva(
                request.user, 
                clase_id
            )
            
            if exito:
                messages.success(request, "¡Reserva realizada con éxito!")
                return redirect('gym_reservas:mis_reservas')
            else:
                messages.error(request, resultado)

        elif 'cancelar' in request.POST:
            # Buscar reserva activa
            try:
                reserva = Reserva.objects.get(
                    socio=request.user, 
                    clase=clase, 
                    estado='confirmada'
                )
                
                # Usar servicio para cancelar con validación RF-004
                exito, mensaje = reserva_service.cancelar_reserva(
                    reserva.id, 
                    request.user
                )
                
                if exito:
                    messages.success(request, mensaje)
                else:
                    messages.error(request, mensaje)
                    
            except Reserva.DoesNotExist:
                messages.error(request, "No se encontró la reserva.")
            
            return redirect('gym_reservas:detalle_clase', clase_id=clase_id)

    # Obtener disponibilidad actualizada
    cupos_service = CuposService()
    disponibilidad = cupos_service.get_disponibilidad_clase(clase_id)
    
    context = {
        'clase': clase,
        'reservado': reservado,
        'disponibilidad': disponibilidad,
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'gym_reservas/class_detail.html', context)


@login_required
def mis_reservas(request):
    """Vista de reservas del usuario logueado"""
    from .services import ReservaRepository
    
    repo = ReservaRepository()
    reservas = repo.get_reservas_activas_socio(request.user)
    
    context = {
        'reservas': reservas,
    }
    return render(request, 'gym_reservas/booking_list.html', context)


@login_required
@require_http_methods(["POST"])
def cancelar_reserva(request, reserva_id):
    """
    Vista para cancelar una reserva
    Implementa RF-004: Cancelación hasta 2 horas antes
    """
    reserva_service = ReservaService()
    
    exito, mensaje = reserva_service.cancelar_reserva(
        reserva_id, 
        request.user
    )
    
    if exito:
        messages.success(request, mensaje)
    else:
        messages.error(request, mensaje)
    
    return redirect('gym_reservas:mis_reservas')


def login_view(request):
    """Vista de login con autenticación"""
    if request.user.is_authenticated:
        return redirect('gym_reservas:index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Autenticar (Django usa bcrypt si está configurado en settings)
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'gym_reservas:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'gym_reservas/login.html')


def register_view(request):
    """Vista de registro con contraseña hasheada"""
    if request.user.is_authenticated:
        return redirect('gym_reservas:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()  # La contraseña se hashea automáticamente
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('gym_reservas:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'gym_reservas/register.html', {'form': form})


def search(request):
    """
    Vista de búsqueda de clases
    RF-002: Búsqueda con filtros
    """
    query = request.GET.get('query', '').strip()
    clases = []
    
    if query:
        clases = Clase.objects.filter(
            Q(nombre__icontains=query) | Q(instructor_nombre__icontains=query),
            fecha__gte=timezone.now().date(),
            estado='programada'
        ).order_by('fecha', 'hora_inicio')
    
    context = {
        'classes': clases,
        'query': query,
    }
    return render(request, 'gym_reservas/search.html', context)


# ============================================================================
# API REST VIEWSETS (Para integración futura o apps móviles)
# ============================================================================

class ClaseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet de solo lectura para clases
    GET /api/clases/ - Lista con filtros
    GET /api/clases/{id}/ - Detalle con disponibilidad
    """
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Clase.objects.filter(
            fecha__gte=timezone.now().date(),
            estado='programada'
        ).select_related('instructor__user', 'sala')
        
        # Filtros opcionales
        tipo = self.request.query_params.get('tipo')
        fecha = self.request.query_params.get('fecha')
        
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if fecha:
            queryset = queryset.filter(fecha=fecha)
        
        return queryset.order_by('fecha', 'hora_inicio')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ClaseDetailSerializer
        return ClaseListSerializer
    
    @action(detail=True, methods=['get'])
    def disponibilidad(self, request, pk=None):
        """
        Endpoint especializado para consultar disponibilidad
        GET /api/clases/{id}/disponibilidad/
        """
        cupos_service = CuposService()
        disponibilidad = cupos_service.get_disponibilidad_clase(pk)
        
        if not disponibilidad:
            return Response(
                {'error': 'Clase no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(disponibilidad)


class ReservaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de reservas
    POST /api/reservas/ - Crear reserva (RF-003)
    DELETE /api/reservas/{id}/ - Cancelar reserva (RF-004)
    GET /api/reservas/ - Mis reservas
    """
    serializer_class = ReservaSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Solo devuelve reservas del usuario autenticado"""
        return Reserva.objects.filter(
            socio=self.request.user,
            estado='confirmada'
        ).select_related('clase').order_by('-fecha_reserva')
    
    def create(self, request, *args, **kwargs):
        """
        Crear reserva con validaciones transaccionales
        Implementa RF-003
        """
        clase_id = request.data.get('clase')
        
        if not clase_id:
            return Response(
                {'error': 'Debe especificar una clase'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reserva_service = ReservaService()
        exito, resultado = reserva_service.crear_reserva(
            request.user,
            clase_id
        )
        
        if exito:
            serializer = self.get_serializer(resultado)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'error': resultado},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Cancelar reserva con validación de tiempo
        Implementa RF-004
        """
        reserva = self.get_object()
        reserva_service = ReservaService()
        
        exito, mensaje = reserva_service.cancelar_reserva(
            reserva.id,
            request.user
        )
        
        if exito:
            return Response(
                {'message': mensaje},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': mensaje},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """
        Devuelve solo reservas activas (futuras)
        GET /api/reservas/activas/
        """
        from .services import ReservaRepository
        
        repo = ReservaRepository()
        reservas = repo.get_reservas_activas_socio(request.user)
        serializer = self.get_serializer(reservas, many=True)
        return Response(serializer.data)


class ReporteViewSet(viewsets.ViewSet):
    """
    ViewSet para reportes administrativos
    Requiere permisos de staff
    """
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Lista los tipos de reportes disponibles"""
        return Response({
            'reportes': [
                'no-shows',
                'asistencia',
            ]
        })
    
    @action(detail=False, methods=['get'])
    def no_shows(self, request):
        """
        Reporte de no-shows
        GET /api/reportes/no-shows/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Permisos insuficientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'Debe especificar fecha_inicio y fecha_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reporte_service = ReporteService()
        datos = reporte_service.generar_reporte_no_shows(
            fecha_inicio,
            fecha_fin
        )
        
        serializer = ReporteNoShowSerializer(datos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def asistencia(self, request):
        """
        Reporte de asistencia por clase
        GET /api/reportes/asistencia/?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD
        """
        if not request.user.is_staff:
            return Response(
                {'error': 'Permisos insuficientes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return Response(
                {'error': 'Debe especificar fecha_inicio y fecha_fin'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reporte_service = ReporteService()
        datos = reporte_service.generar_reporte_asistencia(
            fecha_inicio,
            fecha_fin
        )
        
        serializer = ReporteAsistenciaSerializer(datos, many=True)
        return Response(serializer.data)


# ============================================================================
# VISTAS AJAX PARA DISPONIBILIDAD EN TIEMPO REAL
# ============================================================================

@require_http_methods(["GET"])
def disponibilidad_tiempo_real(request, clase_id):
    """
    Endpoint AJAX para consultar disponibilidad en tiempo real
    GET /gym/ajax/disponibilidad/{clase_id}/
    """
    cupos_service = CuposService()
    disponibilidad = cupos_service.get_disponibilidad_clase(clase_id)
    
    if not disponibilidad:
        return JsonResponse(
            {'error': 'Clase no encontrada'},
            status=404
        )
    
    return JsonResponse(disponibilidad)