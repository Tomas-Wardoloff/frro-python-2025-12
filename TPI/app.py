"""
Q-Sec: Simulador Interactivo del Protocolo BB84
Archivo principal de la aplicación con arquitectura de 3 capas
"""
import os
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv
from views.routes import configure_routes
# Importar la base de datos desde la capa de datos
from datos import db
# Importar TODOS los modelos para que SQLAlchemy los registre
from datos.models import User, SimulationSession
    
# Cargar variables de entorno
load_dotenv()




# Crear la aplicación Flask
app = Flask(__name__, template_folder='views/templates', static_folder='views/static')

# Configuración
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Usar ruta absoluta para la base de datos
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'qsec.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar la base de datos
db.init_app(app)

# Configurar Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario desde la base de datos"""
    from datos import user_repository
    return user_repository.get_user_by_id(int(user_id))


# Configurar las rutas (capa de presentación)

configure_routes(app)


# Crear las tablas si no existen
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
