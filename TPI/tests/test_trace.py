"""
Tests de la traza persistida y de la vista de detalle.

Cubren lo que la Fase 3 agrega: que la traza se guarde, que sobreviva a la
recarga desde la base, y que una sesión sólo la pueda ver su dueño.
"""
import pytest

from business import simulation_controller
from datos import session_repository


def registrar_y_loguear(client, usuario, password='password123'):
    client.post('/register', data={'username': usuario, 'password': password},
                follow_redirects=True)
    client.post('/login', data={'username': usuario, 'password': password},
                follow_redirects=True)
    return client


@pytest.fixture
def logueado(client):
    return registrar_y_loguear(client, 'trazador')


def correr(client, **kwargs):
    body = {'key_length': 200, 'engine': 'analytic'}
    body.update(kwargs)
    return client.post('/api/run-simulation', json=body).get_json()


class TestPersistenciaDeTraza:

    def test_la_traza_se_guarda_con_la_sesion(self, logueado, app):
        datos = correr(logueado)
        sid = datos['session']['id']

        with app.app_context():
            guardada = session_repository.get_session_by_id(sid)
            assert guardada.trace is not None, 'no se persistió la traza'

    def test_la_traza_guardada_coincide_con_la_devuelta(self, logueado, app):
        """Lo que se muestra en vivo y lo que queda guardado son lo mismo."""
        datos = correr(logueado, key_length=150)
        sid = datos['session']['id']
        en_vivo = datos['trace']

        with app.app_context():
            guardada = session_repository.get_session_by_id(sid).trace.to_dict()

        for campo in ('alice_bits', 'alice_bases', 'bob_bases', 'bob_results'):
            assert guardada[campo] == en_vivo[campo], f'difiere en {campo}'

    def test_se_guardan_los_parametros_del_canal(self, logueado, app):
        correr(logueado, noise_rate=7, eve_strategy='intercept_resend',
               eve_fraction=40, engine='analytic')

        with app.app_context():
            s = session_repository.get_user_sessions(1, limit=1)[0]
            assert s.noise_rate == pytest.approx(0.07)
            assert s.eve_strategy == 'intercept_resend'
            assert s.eve_fraction == pytest.approx(0.40)
            assert s.engine == 'analytic'
            assert s.sifted_length is not None

    def test_la_traza_se_recorta_en_corridas_largas(self, logueado, app):
        """Guardar 1000 qubits por fila no aporta; se recorta a 256."""
        datos = correr(logueado, key_length=1000)
        sid = datos['session']['id']

        with app.app_context():
            traza = session_repository.get_session_by_id(sid).trace
            assert traza.truncated is True
            guardada = traza.to_dict()
            assert guardada['shown_bits'] == 256
            assert guardada['total_bits'] == 1000
            assert len(guardada['alice_bits']) == 256

    def test_borrar_la_sesion_borra_su_traza(self, logueado, app):
        """La traza no puede quedar huérfana."""
        from datos.models import SimulationTrace, db

        sid = correr(logueado)['session']['id']
        with app.app_context():
            assert db.session.execute(
                db.select(db.func.count(SimulationTrace.id))
                .filter_by(session_id=sid)
            ).scalar_one() == 1

            session_repository.delete_session(sid)

            assert db.session.execute(
                db.select(db.func.count(SimulationTrace.id))
                .filter_by(session_id=sid)
            ).scalar_one() == 0


class TestCoherenciaDeLaTraza:

    def test_los_indices_cribados_son_los_de_bases_coincidentes(self, logueado):
        t = correr(logueado, key_length=200)['trace']
        esperados = [i for i in range(t['shown_bits'])
                     if t['alice_bases'][i] == t['bob_bases'][i]]
        assert t['sifted_indices'] == esperados

    def test_eve_marca_solo_los_qubits_que_toco(self, logueado):
        t = correr(logueado, key_length=200,
                   eve_strategy='intercept_resend', eve_fraction=50)['trace']
        for i in range(t['shown_bits']):
            if t['intercepted'][i]:
                assert t['eve_bits'][i] in (0, 1)
                assert t['eve_bases'][i] in (0, 1)
            else:
                # -1 marca "Eve no estuvo acá"
                assert t['eve_bits'][i] == -1
                assert t['eve_bases'][i] == -1

    def test_sin_espia_no_hay_nada_interceptado(self, logueado):
        t = correr(logueado, eve_strategy='none')['trace']
        assert not any(t['intercepted'])

    def test_interceptacion_total_toca_todo(self, logueado):
        t = correr(logueado, eve_strategy='intercept_resend',
                   eve_fraction=100)['trace']
        assert all(t['intercepted'])


class TestVistaDeDetalle:

    def test_muestra_la_simulacion(self, logueado):
        sid = correr(logueado)['session']['id']
        resp = logueado.get(f'/simulation/{sid}')
        assert resp.status_code == 200
        assert f'#{sid}'.encode() in resp.data

    def test_incluye_la_tabla_bit_a_bit(self, logueado):
        sid = correr(logueado, key_length=100)['session']['id']
        html = logueado.get(f'/simulation/{sid}').data.decode()
        assert 'Traza del protocolo' in html
        assert 'Base Alice' in html and 'Midió Bob' in html

    def test_una_sesion_inexistente_da_404(self, logueado):
        assert logueado.get('/simulation/999999').status_code == 404

    def test_sin_login_redirige(self, client):
        assert client.get('/simulation/1').status_code == 302

    def test_no_se_puede_ver_la_sesion_de_otro(self, client):
        """El control clave: cambiar el ID en la URL no debe filtrar claves."""
        registrar_y_loguear(client, 'ana')
        sid_ana = correr(client)['session']['id']
        client.get('/logout')

        registrar_y_loguear(client, 'beto')
        resp = client.get(f'/simulation/{sid_ana}')
        assert resp.status_code == 404, 'FUGA: beto pudo ver la sesión de ana'

    def test_el_controller_tambien_valida_la_propiedad(self, logueado, app):
        """La validación vive en negocio, no sólo en la vista."""
        sid = correr(logueado)['session']['id']
        with app.app_context():
            assert simulation_controller.get_simulation_detail(sid, 1) is not None
            assert simulation_controller.get_simulation_detail(sid, 999) is None


class TestSesionesViejasSinTraza:
    """Las corridas anteriores a esta fase no tienen traza y no deben romper."""

    def test_el_detalle_funciona_sin_traza(self, logueado, app):
        with app.app_context():
            s = session_repository.create_session(
                user_id=1, key_length=64, has_eve=False,
                result='secure', final_key='0101', error_rate=0.0,
            )
            sid = s.id
            assert s.trace is None

        resp = logueado.get(f'/simulation/{sid}')
        assert resp.status_code == 200
        assert 'antes de que se guardara la traza'.encode() in resp.data
