"""
Script simple para crear la base de datos directamente con SQLAlchemy
"""
import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Limpiar imports
for mod in list(sys.modules.keys()):
    if 'datos' in mod or 'business' in mod or 'views' in mod or mod == 'app':
        del sys.modules[mod]

print("=== CREACIÓN DIRECTA DE BASE DE DATOS ===\n")

# Importar modelos
from datos import db
from datos.models import User, SimulationSession

# Crear engine directamente
db_path = os.path.join(os.path.dirname(__file__), 'qsec.db')
print(f"Ruta de base de datos: {db_path}")

# Eliminar si existe
if os.path.exists(db_path):
    os.remove(db_path)
    print("Base de datos anterior eliminada")

# Crear engine
engine = create_engine(f'sqlite:///{db_path}', echo=True)
print(f"\nEngine creado: {engine}")

# Crear todas las tablas
print("\n=== CREANDO TABLAS ===")
db.metadata.create_all(bind=engine)

# Verificar
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\n=== TABLAS CREADAS: {tables} ===")

for table in tables:
    print(f"\nTabla: {table}")
    columns = inspector.get_columns(table)
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")

# Verificar que el archivo existe
print(f"\n¿Archivo existe? {os.path.exists(db_path)}")
print(f"Tamaño: {os.path.getsize(db_path) if os.path.exists(db_path) else 0} bytes")
