"""Config de pytest que apunta la suite a Postgres en vez de SQLite."""
import pytest
from sqlalchemy import text

from app import create_app
from config import Config, normalizar_url
from datos import db

URL_PG = normalizar_url('postgres://qsec:qsec@127.0.0.1:55432/qsec_test')


class ConfigPG(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'clave-de-test'
    SQLALCHEMY_DATABASE_URI = URL_PG


@pytest.fixture
def app():
    aplicacion = create_app(ConfigPG, crear_tablas=False)
    with aplicacion.app_context():
        # Esquema limpio por test, como hace la fixture de SQLite
        db.session.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        db.session.commit()
        db.create_all()
        yield aplicacion
        db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()
