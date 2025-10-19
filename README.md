# Sistema de Gestión de Reservas - Energía Total

Sistema web para la gestión automatizada de reservas de clases del gimnasio "Energía Total", desarrollado con Django siguiendo los estándares IEEE 830 y patrones de diseño de software.

## 🎯 Características Principales

### Requerimientos Funcionales Implementados

- **RF-001**: Autenticación segura con RUT y contraseña (bcrypt)
- **RF-002**: Búsqueda de clases con filtros en tiempo real
- **RF-003**: Sistema de reservas con validación transaccional anti-sobrecupos
- **RF-004**: Cancelación de reservas (hasta 2 horas antes)
- **RF-005**: Panel de gestión para instructores

### Requerimientos No Funcionales

- **RNF-001**: Seguridad con bcrypt, CSRF, control de roles
- **RNF-002**: Interfaz responsive y usable
- **RNF-003**: Rendimiento < 3 segundos
- **RNF-004**: Confiabilidad con transacciones ACID

## 🏗️ Arquitectura y Patrones

### Patrones de Diseño Implementados

1. **Strategy Pattern**: Validación modular de reservas
   - Diferentes estrategias de validación (membresía, cupos, límites)
   - Fácil extensión con nuevas validaciones

2. **Repository Pattern**: Acceso centralizado a datos
   - Abstracción de la capa de persistencia
   - Consultas optimizadas y reutilizables

### Algoritmo de Gestión de Cupos

- **Sistema de prioridad para lista de espera**:
  ```
  Prioridad = (días_como_socio × 1) + (reservas_previas × 10)
  ```
- Procesamiento automático al liberarse cupos
- Notificación automática al siguiente en lista

## 📋 Requisitos Previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Virtualenv (recomendado)
- MySQL 8.0+ (para producción) o SQLite (desarrollo)

## 🚀 Instalación

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd energia_total
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos (desarrollo usa SQLite por defecto)
DB_ENGINE=django.db.backends.sqlite3

# Para MySQL en producción:
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=energia_total
# DB_USER=root
# DB_PASSWORD=tu_password
# DB_HOST=localhost
# DB_PORT=3306

# Email (opcional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### 5. Ejecutar Migraciones

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Inicializar Base de Datos con Datos de Ejemplo

```bash
python init_database.py
```

Este script crea:
- Usuario administrador
- 5 socios de ejemplo
- 4 instructores
- Tipos de clases
- Salas del gimnasio
- Clases programadas para 2 semanas
- Reservas de ejemplo

### 7. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

Accede a:
- **Portal Web**: http://127.0.0.1:8000/gym/
- **Panel Admin**: http://127.0.0.1:8000/admin/
- **API REST**: http://127.0.0.1:8000/gym/api/

## 👤 Credenciales de Acceso

### Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin123`

### Socios de Ejemplo
- **Usuario**: `juan.perez` | **Contraseña**: `password123`
- **Usuario**: `maria.gonzalez` | **Contraseña**: `password123`

### Instructores
- **Usuario**: `instructor1` | **Contraseña**: `instructor123`

## 📁 Estructura del Proyecto

```
energia_total/
├── energia_total/          # Configuración principal
│   ├── settings.py        # Configuración (con bcrypt)
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # WSGI para producción
│
├── gym_reservas/          # App principal
│   ├── models.py          # Modelos mejorados
│   ├── views.py           # Vistas con servicios
│   ├── serializers.py     # Serializers REST
│   ├── services.py        # Lógica de negocio (Patrones)
│   ├── admin.py           # Panel admin mejorado
│   ├── urls.py            # URLs de la app
│   ├── forms.py           # Formularios
│   ├── templates/         # Plantillas HTML
│   └── static/            # CSS, JS, imágenes
│
├── init_database.py       # Script de inicialización
├── requirements.txt       # Dependencias
└── manage.py              # CLI de Django
```

## 🔒 Seguridad

### Hashing de Contraseñas (bcrypt)

El sistema usa **bcrypt** como algoritmo principal de hashing:

```python
# settings.py
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    ...
]
```

### Protección CSRF

Todas las vistas POST están protegidas contra CSRF:
- Tokens CSRF en formularios
- Cookies HTTPOnly y Secure en producción

### Control de Acceso

- Roles diferenciados (Socio, Instructor, Admin)
- Decoradores `@login_required` en vistas sensibles
- Permisos verificados en API REST

## 📊 API REST

### Endpoints Principales

#### Clases

```bash
# Listar clases disponibles
GET /gym/api/clases/

# Filtrar por tipo
GET /gym/api/clases/?tipo=yoga

# Filtrar por fecha
GET /gym/api/clases/?fecha=2025-01-15

# Detalle de clase
GET /gym/api/clases/{id}/

# Disponibilidad en tiempo real
GET /gym/api/clases/{id}/disponibilidad/
```

#### Reservas (requiere autenticación)

```bash
# Mis reservas
GET /gym/api/reservas/

# Crear reserva
POST /gym/api/reservas/
{
  "clase": 1
}

# Cancelar reserva
DELETE /gym/api/reservas/{id}/

# Reservas activas
GET /gym/api/reservas/activas/
```

#### Reportes (requiere permisos de staff)

```bash
# Reporte de no-shows
GET /gym/api/reportes/no-shows/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31

# Reporte de asistencia
GET /gym/api/reportes/asistencia/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31
```

## 🧪 Pruebas

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Con coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Reporte HTML en htmlcov/
```

### Tests Implementados

- Tests de modelos (validaciones)
- Tests de servicios (lógica de negocio)
- Tests de vistas (integración)
- Tests de API (endpoints REST)

## 🚀 Despliegue en Producción

### 1. Configurar Variables de Entorno

```env
DEBUG=False
SECRET_KEY=clave-secreta-compleja-aleatoria
ALLOWED_HOSTS=tudominio.com,www.tudominio.com

# MySQL
DB_ENGINE=django.db.backends.mysql
DB_NAME=energia_total
DB_USER=tu_usuario
DB_PASSWORD=tu_password_seguro
DB_HOST=localhost
DB_PORT=3306

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_password_app
```

### 2. Colectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

### 3. Configurar Gunicorn

```bash
gunicorn energia_total.wsgi:application --bind 0.0.0.0:8000
```

### 4. Configurar Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 Cumplimiento de Requerimientos

### Documentación IEEE 830

El sistema cumple con el estándar IEEE 830-1998 para especificación de requisitos:
- ✅ Requerimientos funcionales documentados
- ✅ Requerimientos no funcionales verificables
- ✅ Criterios de aceptación definidos
- ✅ Trazabilidad completa

### Criterios de Aceptación

| Criterio | Estado | Método de Verificación |
|----------|--------|------------------------|
| Eliminación de sobrecupos | ✅ | Validación transaccional con locks |
| Reducción de no-shows 30% | ✅ | Sistema de notificaciones |
| Portal 24/7 | ✅ | Arquitectura en cloud (AWS ready) |
| Tiempo respuesta < 3s | ✅ | Cache y optimización de queries |
| Compatible móvil | ✅ | Diseño responsive |

## 🤝 Contribución

### Equipo de Desarrollo

- **Líder de Proyecto**: Gestión y coordinación
- **Analista de Sistemas**: Diseño y arquitectura
- **Desarrollador/Tester**: Implementación y QA

### Metodología

- Metodología en Cascada
- Rotación de liderazgo cada 4 semanas
- Entregables según cronograma académico

## 📞 Soporte

Para consultas o problemas:
- Email: soporte@energiatotal.cl
- Documentación: `/docs` (próximamente)
- Issues: GitHub Issues

## 📄 Licencia

Proyecto académico - INACAP 2025

---

**Energía Total** - Sistema de Gestión de Reservas  
Versión 1.0.0 | Enero 2025