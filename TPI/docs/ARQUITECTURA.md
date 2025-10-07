# Arquitectura de 3 Capas - Q-Sec

Este documento describe la arquitectura del proyecto siguiendo estrictamente el patrón de 3 capas.

## Estructura de Directorios

```
TPI/
├── app.py                  # Archivo principal de ejecución
├── .env                    # Variables de entorno (NO subir a Git)
├── requirements.txt        # Dependencias
│
├── datos/                  # CAPA DE DATOS
│   ├── __init__.py        # Inicialización de SQLAlchemy
│   ├── models.py          # Modelos de la BD (User, SimulationSession)
│   ├── user_repository.py # Operaciones CRUD de usuarios
│   └── session_repository.py # Operaciones CRUD de sesiones
│
├── business/              # CAPA DE NEGOCIO
│   ├── __init__.py
│   ├── auth_controller.py # Lógica de autenticación
│   └── simulation_controller.py # Lógica del protocolo BB84
│
├── views/                 # CAPA DE PRESENTACIÓN
│   ├── __init__.py
│   ├── forms.py          # Formularios Flask-WTF
│   └── routes.py         # Rutas y controladores Flask
│
├── templates/            # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── simulator.html
│   └── history.html
│
└── static/              # Archivos estáticos
    └── css/
        └── style.css
```

## Descripción de las Capas

### 1. Capa de Datos (`datos/`)

**Responsabilidad**: Acceso y persistencia de datos en la base de datos.

**Características**:
- Contiene los modelos SQLAlchemy (User, SimulationSession)
- Implementa repositorios con operaciones CRUD
- Es la ÚNICA capa que accede directamente a la base de datos
- Retorna objetos de dominio (modelos)

**Archivos**:
- `models.py`: Define las entidades del dominio
- `user_repository.py`: Operaciones sobre usuarios
- `session_repository.py`: Operaciones sobre sesiones de simulación

### 2. Capa de Negocio (`business/`)

**Responsabilidad**: Implementar la lógica de negocio y reglas del sistema.

**Características**:
- Contiene las reglas de negocio (validaciones, cálculos, etc.)
- NO accede directamente a la base de datos
- Llama a la capa de datos cuando necesita persistir o recuperar información
- NO contiene elementos de interfaz (HTML, rutas Flask, etc.)
- Implementa el protocolo BB84 con Qiskit

**Archivos**:
- `auth_controller.py`: Validaciones y lógica de autenticación
- `simulation_controller.py`: Lógica del protocolo BB84

### 3. Capa de Presentación (`views/`)

**Responsabilidad**: Interacción con el usuario y presentación de la información.

**Características**:
- Maneja las rutas HTTP de Flask
- Renderiza templates HTML
- Valida formularios con Flask-WTF
- NO accede directamente a la base de datos
- Solo llama a la capa de negocio

**Archivos**:
- `routes.py`: Define las rutas y vistas de Flask
- `forms.py`: Formularios con validaciones básicas

## Flujo de Datos

```
Usuario → Capa Presentación → Capa Negocio → Capa Datos → Base de Datos
                 ↓                  ↓              ↓
             templates         controllers    repositories
              routes            business         models
```

### Ejemplo: Registro de Usuario

1. **Presentación** (`views/routes.py`):
   - Usuario envía formulario de registro
   - Se valida el formulario con Flask-WTF
   - Llama a `auth_controller.register_user()`

2. **Negocio** (`business/auth_controller.py`):
   - Valida reglas de negocio (longitud mínima, etc.)
   - Llama a `user_repository.create_user()`

3. **Datos** (`datos/user_repository.py`):
   - Verifica que no exista el usuario
   - Crea el objeto User
   - Lo guarda en la base de datos con SQLAlchemy
   - Retorna el objeto User

## Reglas de Separación

### ✅ PERMITIDO

- Presentación → Negocio → Datos
- Capa de datos devuelve objetos del modelo
- Capa de negocio usa objetos del modelo

### ❌ PROHIBIDO

- Presentación → Datos (saltar la capa de negocio)
- Negocio → Presentación
- Datos → Negocio o Presentación
- Importar SQLAlchemy fuera de la capa de datos

## Ventajas de esta Arquitectura

1. **Mantenibilidad**: Cada capa tiene responsabilidades claras
2. **Testabilidad**: Fácil hacer tests unitarios de cada capa
3. **Escalabilidad**: Puedes cambiar la implementación de una capa sin afectar las demás
4. **Reutilización**: La lógica de negocio puede usarse desde diferentes interfaces
5. **Claridad**: El código es más fácil de entender y documentar

## Cumplimiento del Checklist

Esta estructura cumple con todos los requisitos del `checklist_capas.md`:

- ✅ Capa de Presentación NO usa la capa de Datos directamente
- ✅ Capa de Negocio NO contiene elementos de interfaz
- ✅ Capa de Datos es la única que accede a la BD
- ✅ Todas las funciones devuelven objetos de Negocio
- ✅ Hay un archivo principal `app.py` en la raíz
- ✅ Cada capa está en su carpeta correspondiente
