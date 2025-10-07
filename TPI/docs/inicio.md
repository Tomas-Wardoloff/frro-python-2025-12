# Q-Sec: Simulador Interactivo del Protocolo BB84

Este proyecto es un simulador web educativo para el protocolo de criptografía cuántica BB84, desarrollado como Trabajo Práctico Integrador para la materia "Soporte a Gestión de Datos con Programación Visual".

## 🚀 Inicio Rápido

### Pasos para Levantar el Proyecto

```bash
# 1. Clonar el repositorio
git clone https://github.com/Tomas-Wardoloff/frro-python-2025-12.git
cd frro-python-2025-12/TPI

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Crear la base de datos
python reset_db.py

# 6. Ejecutar la aplicación
python app.py

# 7. Abrir en el navegador
# http://localhost:5000
```

¡Listo! Ya puedes registrarte y usar el simulador BB84.

---

## 📋 Configuración Detallada (Opcional)

### 1. Clonar el Repositorio

Primero, clona el repositorio en tu máquina local:
```bash
git clone https://github.com/Tomas-Wardoloff/frro-python-2025-12.git
cd frro-python-2025-12/TPI
```

### 2. Crear el Entorno Virtual

Es fundamental trabajar dentro de un entorno virtual para aislar las dependencias del proyecto.

```bash
python -m venv venv
```

### 3. Activar el Entorno Virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

Deberías ver `(venv)` al inicio de tu línea de comandos.

### 4. Instalar Dependencias

Con el entorno virtual activado, instala todas las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

Esto instalará:
- Flask (framework web)
- SQLAlchemy (ORM para base de datos)
- Qiskit (simulación cuántica)
- Flask-Login (autenticación)
- Y más...

### 5. Inicializar la Base de Datos

Ejecuta el script para crear las tablas en SQLite:

```bash
python reset_db.py
```

Este comando creará el archivo `qsec.db` con las tablas necesarias.

### 6. Ejecutar la Aplicación

Inicia el servidor de desarrollo de Flask:

```bash
python app.py
```

Deberías ver algo como:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

### 7. Acceder a la Aplicación

Abre tu navegador y ve a:
```
http://localhost:5000
```

---

## 🎮 Uso del Simulador

1. **Regístrate**: Crea una cuenta nueva
2. **Inicia sesión**: Usa tus credenciales
3. **Ve al Simulador**: Haz clic en "Simulador" en el menú
4. **Configura la simulación**:
   - Longitud de clave (10-1000 bits)
   - Marca "Incluir espía (Eve)" si quieres simular espionaje
5. **Ejecuta**: Haz clic en "Ejecutar Simulación"
6. **Revisa resultados**: Ve al Dashboard o Historial

---

## 🔧 Solución de Problemas

### Error: "No module named 'flask'"
```bash
# Asegúrate de tener el entorno virtual activado
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### Error: "no such column"
```bash
# Elimina y recrea la base de datos
rm qsec.db  # Linux/Mac
del qsec.db  # Windows
python reset_db.py
```

### La aplicación no inicia
```bash
# Verifica que Python 3.9+ esté instalado
python --version

# Verifica que todas las dependencias estén instaladas
pip list
```

---

## 📁 Estructura del Proyecto

```
TPI/
├── app.py                  # Archivo principal
├── requirements.txt        # Dependencias
├── reset_db.py            # Script de BD
├── qsec.db                # Base de datos (generada)
│
├── datos/                 # Capa de Datos
│   ├── models.py          # Modelos SQLAlchemy
│   ├── user_repository.py
│   └── session_repository.py
│
├── business/              # Capa de Negocio
│   ├── auth_controller.py
│   ├── simulation_controller.py
│   └── bb84_simulation.py # Simulación BB84
│
├── views/                 # Capa de Presentación
│   ├── routes.py          # Rutas Flask
│   └── forms.py           # Formularios
│
├── templates/             # HTML
│   ├── base.html
│   ├── index.html
│   ├── dashboard.html
│   └── ...
│
└── static/               # CSS, JS, imágenes
    └── css/
        └── style.css
```

---

## 📚 Documentación Adicional

- **EXPLICACION_BB84.md**: Explicación detallada del protocolo
- **DIAGRAMAS_BB84.md**: Diagramas visuales del funcionamiento
- **TODO.md**: Lista de tareas pendientes
- **ARQUITECTURA.md**: Documentación de la arquitectura de 3 capas

---

## 🤝 Contribuir

Este es un proyecto académico, pero si encuentras bugs o tienes sugerencias:
1. Crea un issue en GitHub
2. O contacta al equipo de desarrollo

---

## 📄 Licencia

Proyecto desarrollado para fines educativos - UTN FRRO 2025