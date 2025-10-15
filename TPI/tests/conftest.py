"""
conftest.py - Configuración de pytest para los tests del TPI
Se ejecuta automáticamente antes de cada test
"""
import sys
import os

# Agregar el directorio padre (TPI) al path para que pytest pueda encontrar los módulos
tests_dir = os.path.dirname(os.path.abspath(__file__))
tpi_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tpi_dir)

# Configurar variables de entorno para testing
os.environ['FLASK_ENV'] = 'testing'
