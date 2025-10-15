"""
conftest.py - Configuración de pytest para el TPI
"""
import sys
import os

# Agregar el directorio TPI al path para que pytest pueda encontrar los módulos
tpi_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, tpi_dir)

# Configurar variables de entorno para testing
os.environ['FLASK_ENV'] = 'testing'
