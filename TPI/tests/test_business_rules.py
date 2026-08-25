"""
Tests de las reglas de negocio.

El enunciado del TPI pide explícitamente "Test que evalúe que se cumplan las
reglas de negocio en los Métodos de la Clase de Negocio". Hasta acá ningún test
importaba auth_controller ni simulation_controller: lo que había verificaba
SQLAlchemy y el módulo random de Python.

Cada test nombra la regla que valida.
"""
import pytest

from business import auth_controller, otp, simulation_controller
from business.bb84 import UMBRAL_QBER, simulate_bb84
from business.simulation_controller import (
    MAX_KEY_LENGTH,
    MAX_NOISE_RATE,
    MIN_KEY_LENGTH,
)


@pytest.fixture
def contexto(app):
    """Contexto de aplicación con la base lista."""
    return app


# =====================================================================
# RN-1: El nombre de usuario es único y tiene un largo mínimo
# =====================================================================

class TestReglaRegistroDeUsuarios:

    def test_el_usuario_debe_tener_al_menos_3_caracteres(self, contexto):
        r = auth_controller.register_user('ab', 'password123')
        assert r['success'] is False
        assert '3 caracteres' in r['message']

    def test_la_password_debe_tener_al_menos_6_caracteres(self, contexto):
        r = auth_controller.register_user('valido', '12345')
        assert r['success'] is False
        assert '6 caracteres' in r['message']

    def test_el_usuario_no_puede_repetirse(self, contexto):
        assert auth_controller.register_user('unico', 'password123')['success']
        r = auth_controller.register_user('unico', 'otrapassword')
        assert r['success'] is False
        assert 'ya está en uso' in r['message']

    def test_un_registro_valido_crea_el_usuario(self, contexto):
        r = auth_controller.register_user('nuevo', 'password123')
        assert r['success'] is True
        assert r['user'].username == 'nuevo'

    def test_la_password_nunca_se_guarda_en_claro(self, contexto):
        r = auth_controller.register_user('seguro', 'password123')
        assert r['user'].password_hash != 'password123'
        assert 'password123' not in r['user'].password_hash


class TestReglaAutenticacion:

    def test_credenciales_correctas_autentican(self, contexto):
        auth_controller.register_user('juan', 'password123')
        r = auth_controller.authenticate_user('juan', 'password123')
        assert r['success'] is True

    def test_password_incorrecta_no_autentica(self, contexto):
        auth_controller.register_user('juan', 'password123')
        r = auth_controller.authenticate_user('juan', 'incorrecta')
        assert r['success'] is False

    def test_usuario_inexistente_no_autentica(self, contexto):
        r = auth_controller.authenticate_user('fantasma', 'password123')
        assert r['success'] is False

    def test_no_se_revela_si_el_usuario_existe(self, contexto):
        """El mensaje es el mismo en ambos casos, para no filtrar qué usuarios hay."""
        auth_controller.register_user('juan', 'password123')
        a = auth_controller.authenticate_user('juan', 'mala')['message']
        b = auth_controller.authenticate_user('fantasma', 'mala')['message']
        assert a == b

    def test_campos_vacios_rechazados(self, contexto):
        assert auth_controller.authenticate_user('', '')['success'] is False


# =====================================================================
# RN-2: La longitud de clave y los parámetros del canal tienen rangos válidos
# =====================================================================

class TestReglaParametrosDeSimulacion:

    def test_longitud_por_debajo_del_minimo(self, contexto):
        assert simulation_controller.validar_parametros(MIN_KEY_LENGTH - 1) is not None

    def test_longitud_por_encima_del_maximo(self, contexto):
        assert simulation_controller.validar_parametros(MAX_KEY_LENGTH + 1) is not None

    def test_los_extremos_del_rango_son_validos(self, contexto):
        assert simulation_controller.validar_parametros(MIN_KEY_LENGTH) is None
        assert simulation_controller.validar_parametros(MAX_KEY_LENGTH) is None

    def test_ruido_fuera_de_rango(self, contexto):
        assert simulation_controller.validar_parametros(100, noise_rate=-0.1) is not None
        assert simulation_controller.validar_parametros(
            100, noise_rate=MAX_NOISE_RATE + 0.1) is not None

    def test_fraccion_de_eve_fuera_de_rango(self, contexto):
        assert simulation_controller.validar_parametros(100, eve_fraction=1.5) is not None
        assert simulation_controller.validar_parametros(100, eve_fraction=-0.1) is not None


# =====================================================================
# RN-3: La clave se descarta si el QBER supera el umbral
# =====================================================================

class TestReglaUmbralDeQBER:

    def test_por_debajo_del_umbral_la_clave_se_entrega(self):
        r = simulate_bb84(400, has_eve=False, seed=3)
        assert r.error_rate < UMBRAL_QBER
        assert r.result == 'secure'
        assert r.final_key

    def test_por_encima_del_umbral_no_se_entrega_clave(self):
        """Se busca una corrida detectada; la detección es probabilística."""
        comprometida = next(
            r for r in (simulate_bb84(400, has_eve=True, seed=s) for s in range(20))
            if r.result == 'compromised'
        )
        assert comprometida.error_rate >= UMBRAL_QBER
        assert comprometida.final_key is None

    def test_el_ruido_solo_tambien_descarta_la_clave(self):
        """El protocolo no puede distinguir ruido de espionaje: descarta igual."""
        r = simulate_bb84(600, has_eve=False, noise_rate=0.30, seed=1)
        assert r.result == 'compromised'
        assert 'ruido' in r.message.lower()

    def test_los_bits_revelados_salen_de_la_clave(self):
        """Los bits usados para estimar el error se queman: ya son públicos."""
        r = simulate_bb84(400, has_eve=False, seed=5)
        assert r.final_length == r.sifted_length - len(r.sample_indices)


# =====================================================================
# RN-4: El one-time-pad exige clave segura y suficientemente larga
# =====================================================================

class TestReglaCifrado:

    def test_no_se_cifra_con_clave_comprometida(self):
        assert otp.validar('hola', '0' * 500, 'compromised') is not None

    def test_no_se_cifra_si_la_clave_es_mas_corta_que_el_mensaje(self):
        assert otp.validar('hola mundo', '0' * 16, 'secure') is not None

    def test_se_cifra_con_clave_segura_y_suficiente(self):
        assert otp.validar('hola', '0' * 32, 'secure') is None

    def test_hacen_falta_8_bits_por_caracter(self):
        assert otp.bits_necesarios('abcd') == 32
        assert otp.bits_necesarios('') == 0


# =====================================================================
# RN-5: Cada usuario sólo accede a sus propias simulaciones
# =====================================================================

class TestReglaAislamientoEntreUsuarios:

    def _crear_sesion(self, user_id):
        return simulation_controller.run_bb84_simulation(
            user_id, 200, False, engine='analytic'
        )['session']['id']

    def test_el_detalle_solo_lo_ve_el_dueno(self, contexto):
        auth_controller.register_user('duenio', 'password123')
        auth_controller.register_user('otro', 'password123')
        sid = self._crear_sesion(1)

        assert simulation_controller.get_simulation_detail(sid, 1) is not None
        assert simulation_controller.get_simulation_detail(sid, 2) is None

    def test_solo_el_dueno_puede_borrar(self, contexto):
        auth_controller.register_user('duenio', 'password123')
        auth_controller.register_user('otro', 'password123')
        sid = self._crear_sesion(1)

        assert simulation_controller.delete_user_session(sid, 2) is False
        assert simulation_controller.get_simulation_detail(sid, 1) is not None
        assert simulation_controller.delete_user_session(sid, 1) is True

    def test_las_estadisticas_no_mezclan_usuarios(self, contexto):
        auth_controller.register_user('a', 'password123')
        auth_controller.register_user('b', 'password123')
        self._crear_sesion(1)
        self._crear_sesion(1)

        assert simulation_controller.get_user_statistics(1)['total_simulations'] == 2
        assert simulation_controller.get_user_statistics(2)['total_simulations'] == 0


# =====================================================================
# RN-6: Las estadísticas agregadas son consistentes
# =====================================================================

class TestReglaEstadisticas:

    def test_sin_simulaciones_las_metricas_son_cero(self, contexto):
        s = simulation_controller.get_user_statistics(1)
        assert s == {
            'total_simulations': 0, 'secure_simulations': 0,
            'compromised_simulations': 0, 'success_rate': 0.0,
        }

    def test_seguras_mas_comprometidas_es_el_total(self, contexto):
        auth_controller.register_user('conta', 'password123')
        for _ in range(4):
            simulation_controller.run_bb84_simulation(1, 200, False, engine='analytic')

        s = simulation_controller.get_user_statistics(1)
        assert s['secure_simulations'] + s['compromised_simulations'] == s['total_simulations']

    def test_la_tasa_de_exito_es_un_porcentaje(self, contexto):
        auth_controller.register_user('tasa', 'password123')
        for _ in range(3):
            simulation_controller.run_bb84_simulation(1, 200, False, engine='analytic')
        assert 0 <= simulation_controller.get_user_statistics(1)['success_rate'] <= 100
