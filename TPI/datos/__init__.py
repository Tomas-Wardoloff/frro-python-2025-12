# Capa de Datos
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, 'connect')
def _activar_claves_foraneas(conexion, registro):
    """Hace que SQLite valide las claves foráneas.

    SQLite las tiene desactivadas por defecto: acepta insertar una fila que
    apunte a un padre inexistente sin protestar. Postgres no, así que sin este
    pragma el comportamiento local difiere del de producción y los tests dejan
    pasar violaciones de integridad que después aparecen en el deploy.

    En cualquier otro motor no hace nada.
    """
    if conexion.__class__.__module__.startswith('sqlite3'):
        cursor = conexion.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()
