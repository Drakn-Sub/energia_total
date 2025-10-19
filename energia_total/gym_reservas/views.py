# gym_reservas/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from datetime import date
from .models import Clase, Reserva
from .forms import UserRegistrationForm
from django.db.models import Q


def index(request):
    """Vista principal de la página de inicio"""
    context = {
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'gym_reservas/index.html', context)


def lista_clases(request):
    hoy = date.today()
    clases = Clase.objects.filter(fecha__gte=hoy).order_by('fecha', 'hora_inicio')

    tipo = request.GET.get('tipo')
    fecha = request.GET.get('fecha')
    if tipo:
        clases = clases.filter(tipo=tipo)
    if fecha:
        clases = clases.filter(fecha=fecha)

    context = {
        'clases': clases,
        'tipos': Clase.TIPOS_CLASE,
        'user_authenticated': request.user.is_authenticated,
    }
    return render(request, 'gym_reservas/lista_clases.html', context)


def detalle_clase(request, clase_id):
    clase = get_object_or_404(Clase, id=clase_id)
    reservado = False
    
    # Solo verificar reservas si el usuario está autenticado
    if request.user.is_authenticated:
        reservado = Reserva.objects.filter(socio=request.user, clase=clase, estado='confirmada').exists()

    if request.method == 'POST':
        # Solo permitir acciones si está autenticado
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para hacer reservas.")
            return redirect('gym_reservas:login')
            
        if 'reservar' in request.POST:
            if clase.esta_llena:
                messages.error(request, "No hay cupos disponibles.")
            else:
                try:
                    Reserva.objects.create(socio=request.user, clase=clase)
                    messages.success(request, "¡Reserva realizada con éxito!")
                    
                    return redirect('gym_reservas:lista_clases')
                except Exception as e:
                    messages.error(request, f"Error al reservar: {e}")

        elif 'cancelar' in request.POST:
            reserva = Reserva.objects.get(socio=request.user, clase=clase, estado='confirmada')
            reserva.estado = 'cancelada'
            reserva.save()
            messages.success(request, "Reserva cancelada.")
            return redirect('gym_reservas:lista_clases')

    return render(request, 'gym_reservas/class_detail.html', {
        'clase': clase,
        'reservado': reservado,
        'user_authenticated': request.user.is_authenticated,
    })


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(socio=request.user).order_by('-fecha_reserva')
    return render(request, 'gym_reservas/booking_list.html', {'reservas': reservas})


class SignUpView(CreateView):
    form_class = UserRegistrationForm
    success_url = reverse_lazy('gym_reservas:lista_clases')
    template_name = 'gym_reservas/register.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
        return response


def login_view(request):
    # si ya está autenticado redirige al índice
    if request.user.is_authenticated:
        return redirect('gym_reservas:index')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(request.GET.get('next') or 'gym_reservas:index')
        messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'gym_reservas/login.html')


def register_view(request):
    """Vista para el registro de usuarios"""
    if request.user.is_authenticated:
        return redirect('gym_reservas:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, '¡Cuenta creada exitosamente! Ya puedes iniciar sesión.')
            return redirect('gym_reservas:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'gym_reservas/register.html', {'form': form})

def search(request):
    """Vista para buscar clases"""
    query = request.GET.get('query', '').strip()
    classes = []
    if query:
        classes = Clase.objects.filter(
            Q(nombre__icontains=query) |
            Q(instructor__icontains=query)
        ).order_by('fecha', 'hora')
    context = {
        'classes': classes,
    }
    return render(request, 'gym_reservas/search.html', context)
    
@login_required
def cancelar_reserva(request, reserva_id):
    """Vista para cancelar una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id, socio=request.user)
    if request.method == 'POST':
        reserva.estado = 'cancelada'
        reserva.save()
        messages.success(request, "Reserva cancelada con éxito.")
    return redirect('gym_reservas:mis_reservas')