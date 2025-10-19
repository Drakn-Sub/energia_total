from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'gym_reservas'

# Router para API REST
router = DefaultRouter()
router.register(r'clases', views.ClaseViewSet, basename='clase')
router.register(r'reservas', views.ReservaViewSet, basename='reserva')
router.register(r'reportes', views.ReporteViewSet, basename='reporte')

urlpatterns = [
    # ========================================================================
    # RUTAS DE TEMPLATES (Compatibilidad con templates existentes)
    # ========================================================================
    
    # Página principal
    path('', views.index, name='index'),
    
    # Clases
    path('clases/', views.lista_clases, name='lista_clases'),
    path('clases/<int:clase_id>/', views.detalle_clase, name='detalle_clase'),
    path('search/', views.search, name='search'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    
    # Reservas
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    
    # ========================================================================
    # API REST (Para integraciones futuras)
    # ========================================================================
    path('api/', include(router.urls)),
    
    # ========================================================================
    # AJAX ENDPOINTS (Para funcionalidad en tiempo real)
    # ========================================================================
    path('ajax/disponibilidad/<int:clase_id>/', 
         views.disponibilidad_tiempo_real, 
         name='disponibilidad_ajax'),
]