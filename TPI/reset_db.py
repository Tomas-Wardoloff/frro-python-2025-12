"""
Script para inicializar/resetear la base de datos
Elimina la BD anterior y crea las tablas con la nueva estructura
"""
import os
import sys

# Limpiar módulos cacheados para asegurar que se usen los modelos correctos
modules_to_clear = ['datos', 'datos.models', 'business', 'views', 'app']
for mod in modules_to_clear:
    if mod in sys.modules:
        del sys.modules[mod]

from app import app, db
# Importar explícitamente los modelos para que SQLAlchemy los registre
from datos.models import User, SimulationSession

# Ruta a la base de datos
db_path = os.path.join(os.path.dirname(__file__), 'qsec.db')

# Eliminar la base de datos anterior si existe
if os.path.exists(db_path):
    print(f"⚠️  Eliminando base de datos anterior: {db_path}")
    os.remove(db_path)
    print("✅ Base de datos eliminada")

# Crear las tablas nuevas
with app.app_context():
    print("\n🔨 Creando nuevas tablas...")
    
    # Verificar que los modelos tienen todas las columnas
    print("\n📝 Verificando modelos antes de crear tablas:")
    print(f"   User: {list(User.__table__.columns.keys())}")
    print(f"   SimulationSession: {list(SimulationSession.__table__.columns.keys())}")
    
    db.create_all()
    print("\n✅ Tablas creadas exitosamente")
    
    # Verificar las tablas creadas
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n📋 Tablas en la base de datos: {tables}")
    
    for table in tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        print(f"   - {table}: {columns}")

print("\n✨ ¡Listo! La base de datos ha sido inicializada correctamente.")
print("   Puedes ejecutar la aplicación con: python app.py")
