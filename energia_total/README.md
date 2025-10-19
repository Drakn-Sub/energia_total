# Proyecto de Django: energia_total

Este proyecto es una aplicación de gestión de reservas para un gimnasio, que permite a los usuarios buscar, reservar y cancelar clases, así como visualizar la disponibilidad en tiempo real.

## Estructura del Proyecto

```
energia_total/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env.example
├── README.md
├── energia_total/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── gym_reservas/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── tests.py
    ├── migrations/
    │   └── __init__.py
    ├── templates/
    │   └── gym_reservas/
    │       ├── base.html
    │       ├── index.html
    │       ├── search.html
    │       ├── class_detail.html
    │       ├── booking_confirm.html
    │       ├── booking_list.html
    │       ├── availability.html
    │       ├── login.html
    │       └── register.html
    └── static/
        └── gym_reservas/
            ├── css/
            │   └── styles.css
            └── js/
                └── realtime.js
```

## Funcionalidades

- **Búsqueda de Clases**: Los usuarios pueden buscar clases disponibles según diferentes criterios.
- **Reservas**: Los usuarios pueden reservar clases y recibir confirmaciones.
- **Cancelación de Reservas**: Los usuarios pueden cancelar sus reservas.
- **Disponibilidad en Tiempo Real**: Visualización de la disponibilidad de clases en tiempo real.
- **Autenticación de Usuarios**: Registro e inicio de sesión para gestionar reservas.

## Requisitos

Asegúrate de tener instaladas las siguientes dependencias:

- Django
- Otras dependencias necesarias que se especificarán en `requirements.txt`.

## Configuración

1. Clona el repositorio.
2. Crea un entorno virtual y actívalo.
3. Instala las dependencias con `pip install -r requirements.txt`.
4. Configura las variables de entorno en un archivo `.env` basado en `.env.example`.
5. Realiza las migraciones de la base de datos con `python manage.py migrate`.
6. Inicia el servidor de desarrollo con `python manage.py runserver`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para discutir cambios.

## Licencia

Este proyecto está bajo la Licencia MIT.