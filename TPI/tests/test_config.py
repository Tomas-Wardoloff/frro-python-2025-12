"""
Tests de la configuración por entorno.

Son los que cubren lo que puede fallar recién en producción, donde es caro
descubrirlo.
"""
import pytest

from config import (
    CLAVE_DE_DESARROLLO,
    DesarrolloConfig,
    ProduccionConfig,
    TestingConfig,
    normalizar_url,
    obtener_config,
)


class TestUrlDeBaseDeDatos:

    def test_corrige_el_esquema_de_render_y_heroku(self):
        """Render y Heroku entregan postgres://, que SQLAlchemy 2.0 rechaza."""
        assert normalizar_url('postgres://u:p@host/db') == 'postgresql://u:p@host/db'

    def test_no_toca_una_url_ya_correcta(self):
        url = 'postgresql://u:p@host/db'
        assert normalizar_url(url) == url

    def test_no_toca_sqlite(self):
        assert normalizar_url('sqlite:///qsec.db') == 'sqlite:///qsec.db'

    def test_tolera_none(self):
        assert normalizar_url(None) is None

    def test_solo_reemplaza_el_prefijo(self):
        """Un 'postgres://' dentro de la contraseña no debe alterarse."""
        url = 'postgres://user:postgres://x@host/db'
        assert url.count('postgresql://') == 0
        assert normalizar_url(url).count('postgresql://') == 1


class TestConfiguracionDeProduccion:

    def test_falla_si_falta_la_secret_key(self, monkeypatch):
        """Arrancar con la clave de desarrollo permitiría falsificar sesiones."""
        monkeypatch.setattr(ProduccionConfig, 'SECRET_KEY', CLAVE_DE_DESARROLLO)
        with pytest.raises(RuntimeError, match='SECRET_KEY'):
            ProduccionConfig()

    def test_arranca_con_una_secret_key_propia(self, monkeypatch):
        monkeypatch.setattr(ProduccionConfig, 'SECRET_KEY', 'una-clave-de-verdad')
        cfg = ProduccionConfig()
        assert cfg.DEBUG is False
        assert cfg.SESSION_COOKIE_SECURE is True

    def test_las_cookies_van_por_https(self, monkeypatch):
        monkeypatch.setattr(ProduccionConfig, 'SECRET_KEY', 'x')
        assert ProduccionConfig().SESSION_COOKIE_SECURE is True


class TestConfiguracionDeTesting:

    def test_la_base_esta_en_memoria(self):
        """Ninguna corrida de tests puede tocar un archivo real."""
        assert TestingConfig.SQLALCHEMY_DATABASE_URI == 'sqlite://'

    def test_el_csrf_esta_desactivado(self):
        assert TestingConfig.WTF_CSRF_ENABLED is False


class TestSeleccionDeEntorno:

    def test_por_defecto_desarrollo(self, monkeypatch):
        monkeypatch.delenv('FLASK_ENV', raising=False)
        assert obtener_config() is DesarrolloConfig

    def test_un_entorno_desconocido_cae_en_desarrollo(self):
        assert obtener_config('inventado') is DesarrolloConfig

    def test_se_puede_pedir_testing(self):
        assert obtener_config('testing') is TestingConfig


class TestFactoryDeAplicacion:

    def test_cada_llamada_devuelve_una_app_independiente(self):
        from app import create_app
        a, b = create_app(TestingConfig), create_app(TestingConfig)
        assert a is not b

    def test_registra_todas_las_rutas(self):
        from app import create_app
        app = create_app(TestingConfig)
        endpoints = {r.endpoint for r in app.url_map.iter_rules()}
        for esperado in ('home', 'login', 'register', 'dashboard', 'simulator',
                         'history', 'simulation_result', 'run_simulation',
                         'analytics', 'delete_simulation', 'export_simulation',
                         'encrypt_message'):
            assert esperado in endpoints, f'falta la ruta {esperado}'

    def test_puede_construirse_sin_crear_tablas(self):
        """crear_tablas=False evita que importar la app escriba en disco."""
        from app import create_app
        assert create_app(TestingConfig, crear_tablas=False) is not None


class TestAislamientoDeLaSuite:
    """Guardas para que los tests no puedan tocar la base de desarrollo.

    Este control existe por un incidente real: cuando ``app.py`` pasó a usar
    una factory, los archivos de test que todavía hacían ``from app import app``
    quedaron usando la instancia global —apuntada a ``qsec.db``— en lugar de la
    fixture aislada, y empezaron a escribir en la base de desarrollo.
    """

    def test_ningun_test_usa_la_instancia_global_de_la_app(self):
        """Los tests tienen que pedir la app por fixture, no importarla."""
        import pathlib
        import re

        directorio = pathlib.Path(__file__).parent
        patron = re.compile(r'^from app import .*\bapp\b', re.MULTILINE)

        culpables = []
        for archivo in directorio.glob('test_*.py'):
            texto = archivo.read_text(encoding='utf-8')
            # create_app es la factory y sí se puede importar
            for linea in patron.findall(texto):
                if 'create_app' not in linea:
                    culpables.append(f'{archivo.name}: {linea}')

        detalle = '\n'.join(culpables)
        assert not culpables, (
            f'Estos tests usan la app global, que apunta a la base real:\n{detalle}'
        )

    def test_la_config_de_test_nunca_apunta_a_un_archivo(self, app):
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        assert uri in ('sqlite://', 'sqlite:///:memory:')
        assert '.db' not in uri
