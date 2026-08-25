"""
Configuración de la aplicación por entorno.

Separar la configuración del código permite que los tests corran contra una
base en memoria sin tocar archivos reales, y que producción exija una
SECRET_KEY de verdad en lugar de caer silenciosamente en la de desarrollo.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

CLAVE_DE_DESARROLLO = 'dev-secret-key-change-in-production'


# Driver de PostgreSQL que se usa. SQLAlchemy asume psycopg2 cuando la URL
# dice sólo "postgresql://", pero el que está en requirements.txt es psycopg 3,
# que se selecciona con "postgresql+psycopg://". Sin esto la app arranca en
# local con SQLite y falla en producción con "No module named 'psycopg2'".
DRIVER_POSTGRES = 'postgresql+psycopg'


def normalizar_url(url):
    """
    Corrige el esquema de las URL de Postgres.

    Hace dos cosas:

    1. Render y Heroku entregan ``DATABASE_URL`` empezando con ``postgres://``,
       un esquema que SQLAlchemy 2.0 ya no reconoce y que hace fallar el
       arranque con "Can't load plugin".
    2. Fija el driver psycopg 3, que es el que está en requirements.txt. Sin
       esto SQLAlchemy busca psycopg2, que no está instalado.

    Una URL que ya indique driver (``postgresql+asyncpg://``, por ejemplo) se
    respeta tal cual.
    """
    if not url:
        return url

    if url.startswith('postgres://'):
        return DRIVER_POSTGRES + url[len('postgres'):]

    # "postgresql://" sin driver explícito
    if url.startswith('postgresql://'):
        return DRIVER_POSTGRES + url[len('postgresql'):]

    return url


class Config:
    """Configuración base, común a todos los entornos."""

    SECRET_KEY = os.getenv('SECRET_KEY', CLAVE_DE_DESARROLLO)
    SQLALCHEMY_DATABASE_URI = normalizar_url(
        os.getenv('DATABASE_URL') or f'sqlite:///{os.path.join(BASE_DIR, "qsec.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # La app se sirve detrás de HTTPS en producción
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'


class DesarrolloConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    # Base en memoria: los tests nunca deben tocar un archivo real
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'clave-de-test'


class ProduccionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    def __init__(self):
        # Fallar al arrancar es preferible a servir en producción con la clave
        # de desarrollo, que permitiría falsificar cookies de sesión.
        if self.SECRET_KEY == CLAVE_DE_DESARROLLO:
            raise RuntimeError(
                'Falta definir SECRET_KEY. En producción no se puede usar la '
                'clave de desarrollo: con ella cualquiera puede falsificar '
                'cookies de sesión.'
            )


CONFIGURACIONES = {
    'development': DesarrolloConfig,
    'testing': TestingConfig,
    'production': ProduccionConfig,
}


def obtener_config(nombre=None):
    """Devuelve la clase de configuración del entorno pedido."""
    nombre = nombre or os.getenv('FLASK_ENV', 'development')
    clase = CONFIGURACIONES.get(nombre, DesarrolloConfig)
    # ProduccionConfig valida en __init__, así que se instancia
    return clase() if nombre == 'production' else clase
