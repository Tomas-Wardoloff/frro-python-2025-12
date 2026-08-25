"""
Configuración compartida de pytest.

Cada test recibe una aplicación construida por la factory con
``TestingConfig``, cuya base vive en memoria. Eso garantiza que la suite no
pueda tocar ``qsec.db`` ni ningún otro archivo real.

Antes esto no era así: ``app.py`` creaba la app y llamaba a ``db.create_all()``
a nivel de módulo, de modo que el engine de SQLAlchemy quedaba ligado al
archivo real apenas se importaba. Las fixtures cambiaban
``SQLALCHEMY_DATABASE_URI`` a ``:memory:`` *después* de ese import, cuando ya
no tenía efecto, y el ``db.drop_all()`` del teardown terminaba borrando la base
de desarrollo. La suite daba verde mientras destruía los datos.
"""
import pytest

from app import create_app
from config import TestingConfig
from datos import db


@pytest.fixture
def app():
    """Aplicación aislada, con una base en memoria por test."""
    aplicacion = create_app(TestingConfig, crear_tablas=False)

    uri = aplicacion.config['SQLALCHEMY_DATABASE_URI']
    # Red de seguridad: si alguna vez la configuración de test dejara de
    # apuntar a memoria, se corta antes de crear o borrar nada.
    assert uri in ('sqlite://', 'sqlite:///:memory:'), (
        f'Los tests no pueden correr contra una base real ({uri!r})'
    )

    with aplicacion.app_context():
        db.create_all()
        yield aplicacion
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Cliente HTTP de prueba."""
    return app.test_client()
