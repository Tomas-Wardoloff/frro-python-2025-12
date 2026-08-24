"""
Configuración compartida de pytest.

IMPORTANTE — por qué se toca el entorno antes de importar la app:

``app.py`` ejecuta ``db.create_all()`` a nivel de módulo, lo que liga el engine
de SQLAlchemy a la base indicada por ``DATABASE_URL`` en el momento del import.
Flask-SQLAlchemy cachea ese engine, así que cambiar
``SQLALCHEMY_DATABASE_URI`` en una fixture *después* del import no tiene ningún
efecto: la conexión sigue apuntando al archivo real.

Las fixtures anteriores hacían exactamente eso y terminaban corriendo
``db.drop_all()`` contra ``qsec.db``. Resultado: correr la suite borraba la base
de desarrollo y los tests igual daban verde.

Fijar ``DATABASE_URL`` acá, antes del import, garantiza que los tests nunca
toquen un archivo real. La fixture además lo verifica antes de crear tablas.
"""
import os

# Tiene que ir antes de importar app (ver explicación de arriba).
os.environ['DATABASE_URL'] = 'sqlite://'          # base en memoria
os.environ.setdefault('SECRET_KEY', 'clave-de-test')
os.environ['FLASK_ENV'] = 'testing'

import pytest  # noqa: E402

from app import app as flask_app  # noqa: E402
from datos import db  # noqa: E402


def _es_en_memoria(uri):
    return uri in ('sqlite://', 'sqlite:///:memory:')


@pytest.fixture
def app():
    """App configurada para tests, con una base en memoria por test."""
    flask_app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    uri = flask_app.config['SQLALCHEMY_DATABASE_URI']
    # Red de seguridad: si por lo que sea la app quedó apuntando a un archivo,
    # se aborta antes de crear o borrar nada.
    assert _es_en_memoria(uri), (
        f'Los tests no pueden correr contra una base real ({uri!r}). '
        'Revisá que conftest.py se importe antes que app.'
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba."""
    return app.test_client()
