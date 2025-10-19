from django.urls import path
from . import views

app_name = 'gym_reservas'

urlpatterns = [
    path('', views.index, name='index'),
    path('clases/', views.lista_clases, name='lista_clases'),
    path('clases/<int:clase_id>/', views.detalle_clase, name='detalle_clase'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('mis-reservas/', views.mis_reservas, name='mis_reservas'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('search/', views.search, name='search'),
]