from django.contrib import admin
from django.db import models as dj_models
from .models import Clase, Reserva

@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    # Mostrar todos los campos reales del modelo para evitar errores si cambian los nombres
    list_display = [f.name for f in Clase._meta.fields]
    # Añadir filtros sólo para campos de tipo fecha/datetime existentes
    list_filter = [f.name for f in Clase._meta.fields if isinstance(f, (dj_models.DateField, dj_models.DateTimeField))]
    # Búsqueda sobre campos texto si existen
    search_fields = [f.name for f in Clase._meta.fields if isinstance(f, (dj_models.CharField, dj_models.TextField))]

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = [f.name for f in Reserva._meta.fields]
    search_fields = [f.name for f in Reserva._meta.fields if isinstance(f, (dj_models.CharField, dj_models.TextField))]