# init_db.py

from app import app, db

with app.app_context():
    print("Creando todas las tablas de la base de datos...")
    db.create_all()
    print("¡Listo!")
