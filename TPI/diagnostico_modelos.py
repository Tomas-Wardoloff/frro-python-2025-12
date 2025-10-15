"""
Script de diagnóstico para verificar los modelos
"""
import sys
import os

# Limpiar cualquier importación anterior
if 'datos' in sys.modules:
    del sys.modules['datos']
if 'datos.models' in sys.modules:
    del sys.modules['datos.models']

print("=== DIAGNÓSTICO DE MODELOS ===\n")

# Importar y verificar
from datos.models import User, SimulationSession

print("1. Verificando clase User:")
print("   Columnas definidas en User:")
for attr_name in dir(User):
    attr = getattr(User, attr_name)
    if hasattr(attr, 'type'):
        print(f"   - {attr_name}: {attr.type}")

print("\n2. Verificando clase SimulationSession:")
print("   Columnas definidas en SimulationSession:")
for attr_name in dir(SimulationSession):
    attr = getattr(SimulationSession, attr_name)
    if hasattr(attr, 'type'):
        print(f"   - {attr_name}: {attr.type}")

print("\n3. Verificando __table__ de User:")
if hasattr(User, '__table__'):
    print(f"   Columnas en __table__: {list(User.__table__.columns.keys())}")

print("\n4. Verificando __table__ de SimulationSession:")
if hasattr(SimulationSession, '__table__'):
    print(f"   Columnas en __table__: {list(SimulationSession.__table__.columns.keys())}")
