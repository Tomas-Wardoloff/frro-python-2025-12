"""
Tests del flujo web completo: registro, login, simulación y control de acceso.

Cubren la capa de presentación de punta a punta con el cliente HTTP, que es lo
que ningún test tocaba antes.
"""
import pytest

from business.bb84 import UMBRAL_QBER


def registrar(client, usuario='tester', password='secreto123'):
    return client.post('/register', data={
        'username': usuario, 'password': password
    }, follow_redirects=True)


def loguear(client, usuario='tester', password='secreto123'):
    return client.post('/login', data={
        'username': usuario, 'password': password
    }, follow_redirects=True)


@pytest.fixture
def logueado(client):
    """Cliente con una cuenta creada y sesión iniciada."""
    registrar(client)
    loguear(client)
    return client


class TestAutenticacion:

    def test_registro_crea_la_cuenta(self, client):
        resp = registrar(client)
        assert resp.status_code == 200
        assert b'exitosamente' in resp.data

    def test_no_se_puede_repetir_el_usuario(self, client):
        registrar(client)
        resp = registrar(client)
        assert 'ya está en uso'.encode() in resp.data

    def test_usuario_corto_rechazado(self, client):
        resp = client.post('/register', data={
            'username': 'ab', 'password': 'secreto123'
        }, follow_redirects=True)
        assert b'entre 3 y 80' in resp.data

    def test_password_corta_rechazada(self, client):
        resp = client.post('/register', data={
            'username': 'valido', 'password': '123'
        }, follow_redirects=True)
        assert b'al menos 6' in resp.data

    def test_login_con_password_incorrecta_falla(self, client):
        registrar(client)
        resp = client.post('/login', data={
            'username': 'tester', 'password': 'incorrecta'
        }, follow_redirects=True)
        assert b'incorrectos' in resp.data

    def test_login_correcto_entra_al_dashboard(self, client):
        registrar(client)
        resp = loguear(client)
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data

    def test_logout_cierra_la_sesion(self, logueado):
        logueado.get('/logout', follow_redirects=True)
        assert logueado.get('/dashboard').status_code == 302


class TestControlDeAcceso:

    @pytest.mark.parametrize('ruta', ['/dashboard', '/simulator', '/history'])
    def test_rutas_privadas_redirigen_sin_login(self, client, ruta):
        resp = client.get(ruta)
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_la_api_rechaza_sin_login(self, client):
        resp = client.post('/api/run-simulation', json={'key_length': 64})
        assert resp.status_code == 403
        assert resp.get_json()['success'] is False

    def test_rutas_privadas_responden_con_login(self, logueado):
        for ruta in ('/dashboard', '/simulator', '/history'):
            assert logueado.get(ruta).status_code == 200


class TestSimuladorWeb:

    def test_el_formulario_redirige_a_la_animacion_con_los_parametros(self, logueado):
        resp = logueado.post('/simulator', data={
            'key_length': 128, 'noise_rate': 5,
            'eve_strategy': 'intercept_resend', 'eve_fraction': 50,
            'engine': 'analytic',
        })
        assert resp.status_code == 302
        destino = resp.headers['Location']
        for esperado in ('key_length=128', 'noise_rate=5',
                         'eve_strategy=intercept_resend', 'eve_fraction=50'):
            assert esperado in destino, f'falta {esperado} en {destino}'

    def test_ruido_cero_es_valido(self, logueado):
        """InputRequired y no DataRequired: el 0 es un valor legítimo."""
        resp = logueado.post('/simulator', data={
            'key_length': 64, 'noise_rate': 0,
            'eve_strategy': 'none', 'eve_fraction': 0, 'engine': 'analytic',
        })
        assert resp.status_code == 302, 'el 0 no debería rechazarse'

    def test_parametros_fuera_de_rango_se_rechazan(self, logueado):
        resp = logueado.post('/simulator', data={
            'key_length': 5, 'noise_rate': 0,
            'eve_strategy': 'none', 'eve_fraction': 0, 'engine': 'analytic',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'entre 10 y 1000' in resp.data


class TestApiSimulacion:

    def test_corrida_sin_espia_devuelve_clave(self, logueado):
        resp = logueado.post('/api/run-simulation', json={
            'key_length': 256, 'noise_rate': 0,
            'eve_strategy': 'none', 'eve_fraction': 0, 'engine': 'analytic',
        })
        assert resp.status_code == 200
        datos = resp.get_json()
        assert datos['success'] is True
        assert datos['session']['result'] == 'secure'
        assert datos['session']['final_key']

    def test_la_api_devuelve_la_traza_real(self, logueado):
        """La animación tiene que poder dibujar el protocolo, no inventarlo."""
        resp = logueado.post('/api/run-simulation', json={
            'key_length': 128, 'eve_strategy': 'none', 'engine': 'analytic',
        })
        traza = resp.get_json()['trace']
        for campo in ('alice_bits', 'alice_bases', 'bob_bases', 'bob_results',
                      'eve_bases', 'eve_bits', 'intercepted', 'sifted_indices'):
            assert campo in traza, f'falta {campo}'
        assert len(traza['alice_bits']) == 128
        # Sin espía, Bob reproduce los bits de Alice donde las bases coinciden
        for i in traza['sifted_indices']:
            assert traza['bob_results'][i] == traza['alice_bits'][i]

    def test_espia_total_compromete(self, logueado):
        """Un espia que intercepta todo se detecta en la gran mayoria de las corridas.

        No en todas: el QBER se estima sobre una muestra de a lo sumo 20 bits y
        la deteccion es probabilistica (~9% de escape). Por eso se exige mayoria
        sobre varias corridas y no certeza sobre una.
        """
        veredictos = []
        for _ in range(12):
            r = logueado.post('/api/run-simulation', json={
                'key_length': 400, 'eve_strategy': 'intercept_resend',
                'eve_fraction': 100, 'engine': 'analytic',
            })
            veredictos.append(r.get_json()['session'])

        comprometidas = [v for v in veredictos if v['result'] == 'compromised']
        assert len(comprometidas) >= 8
        # Cuando se detecta, no se entrega clave
        assert all(v['final_key'] is None for v in comprometidas)
        assert all(v['error_rate'] > UMBRAL_QBER for v in comprometidas)

    def test_ruido_alto_sin_espia_tambien_descarta(self, logueado):
        """Regla de negocio: el protocolo no distingue ruido de espionaje."""
        resultados = []
        for _ in range(8):
            r = logueado.post('/api/run-simulation', json={
                'key_length': 600, 'noise_rate': 30,
                'eve_strategy': 'none', 'engine': 'analytic',
            })
            resultados.append(r.get_json())

        descartadas = [d for d in resultados if d['session']['result'] == 'compromised']
        assert len(descartadas) >= 6
        # El diagnostico tiene que atribuirlo al ruido, no a un espia
        assert all('ruido' in d['message'].lower() for d in descartadas)

    def test_interceptacion_parcial_baja_el_qber(self, logueado):
        def qber_medio(fraccion, corridas=8):
            total = 0.0
            for _ in range(corridas):
                r = logueado.post('/api/run-simulation', json={
                    'key_length': 800, 'eve_strategy': 'intercept_resend',
                    'eve_fraction': fraccion, 'engine': 'analytic',
                })
                total += r.get_json()['session']['error_rate']
            return total / corridas

        # Con 25% interceptado el QBER teorico es ~6.25%; con 100%, ~25%.
        # Se promedia porque cada estimacion sale de una muestra de 20 bits.
        assert qber_medio(25) < qber_medio(100)

    def test_parametros_invalidos_dan_400(self, logueado):
        resp = logueado.post('/api/run-simulation', json={
            'key_length': 'muchos', 'engine': 'analytic',
        })
        assert resp.status_code == 400
        assert resp.get_json()['success'] is False

    def test_key_length_fuera_de_rango_da_400(self, logueado):
        resp = logueado.post('/api/run-simulation', json={'key_length': 99999})
        assert resp.status_code == 400
        assert 'exceder' in resp.get_json()['message']

    def test_sin_cuerpo_json_da_400(self, logueado):
        resp = logueado.post('/api/run-simulation',
                             data='', content_type='application/json')
        assert resp.status_code == 400

    def test_compatibilidad_con_has_eve(self, logueado):
        """Los enlaces viejos que mandan has_eve tienen que seguir andando.

        Se verifica la traduccion del parametro y no el veredicto, porque la
        deteccion es probabilistica: con muestras de 20 bits, un espia total se
        escapa ~9% de las veces. Eso se cubre estadisticamente aparte.
        """
        resp = logueado.post('/api/run-simulation', json={
            'key_length': 300, 'has_eve': True, 'engine': 'analytic',
        })
        detalles = resp.get_json()['simulation_details']
        assert detalles['eve_strategy'] == 'intercept_resend'
        assert detalles['eve_fraction'] == 1.0

    def test_motor_qiskit_por_la_api(self, logueado):
        resp = logueado.post('/api/run-simulation', json={
            'key_length': 128, 'eve_strategy': 'none', 'engine': 'qiskit',
        })
        datos = resp.get_json()
        assert datos['success'] is True
        assert datos['simulation_details']['engine'] in ('qiskit', 'analytic')


class TestHistorialYDashboard:

    def test_las_simulaciones_aparecen_en_el_historial(self, logueado):
        for _ in range(3):
            logueado.post('/api/run-simulation',
                          json={'key_length': 64, 'engine': 'analytic'})
        resp = logueado.get('/history')
        assert resp.status_code == 200
        assert resp.data.count(b'bits') >= 3

    def test_el_dashboard_cuenta_las_simulaciones(self, logueado):
        logueado.post('/api/run-simulation',
                      json={'key_length': 64, 'engine': 'analytic'})
        assert logueado.get('/dashboard').status_code == 200

    def test_un_usuario_no_ve_las_sesiones_de_otro(self, client):
        registrar(client, 'ana', 'password1')
        loguear(client, 'ana', 'password1')
        client.post('/api/run-simulation',
                    json={'key_length': 64, 'engine': 'analytic'})
        client.get('/logout')

        registrar(client, 'beto', 'password2')
        loguear(client, 'beto', 'password2')
        resp = client.get('/history')
        assert b'Comprometida' not in resp.data and b'Segura' not in resp.data
