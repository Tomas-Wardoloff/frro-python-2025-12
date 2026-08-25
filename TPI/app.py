"""
Q-Sec: Simulador Interactivo del Protocolo BB84
Archivo principal de la aplicación con arquitectura de 3 capas
"""
import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager

from config import obtener_config
# Importar la base de datos desde la capa de datos
from datos import db
# Importar TODOS los modelos para que SQLAlchemy los registre.
# El import es necesario por su efecto colateral, no por los nombres.
from datos.models import SimulationSession, SimulationTrace, User  # noqa: F401
from views.routes import configure_routes

# Cargar variables de entorno
load_dotenv()

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario desde la base de datos"""
    from datos import user_repository
    return user_repository.get_user_by_id(int(user_id))


def create_app(config=None, crear_tablas=True):
    """
    Construye una instancia de la aplicación.

    Antes la app era un objeto global que se creaba al importar el módulo, y
    ``db.create_all()`` corría a nivel de módulo: importar la app escribía en
    disco. Eso hacía además que los tests no pudieran redirigir la base a
    memoria, porque para cuando la fixture cambiaba la configuración el engine
    de SQLAlchemy ya estaba ligado al archivo real.

    Args:
        config: clase o instancia de configuración. Si se omite se deduce de
            la variable de entorno FLASK_ENV.
        crear_tablas (bool): si crear el esquema al construir la app.

    Returns:
        Flask: la aplicación configurada
    """
    app = Flask(
        __name__,
        template_folder='views/templates',
        static_folder='views/static',
    )
    app.config.from_object(config or obtener_config())

    db.init_app(app)
    login_manager.init_app(app)

    # Capa de presentación
    configure_routes(app)

    if crear_tablas:
        with app.app_context():
            db.create_all()

    return app


# Instancia por defecto, para `python app.py`, `flask run` y gunicorn
app = create_app()


if __name__ == '__main__':
    app.run(
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
    )
