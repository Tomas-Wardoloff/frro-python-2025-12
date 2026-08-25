"""
Tests de one-time-pad, analítica y gestión de sesiones.
"""
import json

import pytest

from business import otp, simulation_controller


def registrar_y_loguear(client, usuario, password='password123'):
    client.post('/register', data={'username': usuario, 'password': password},
                follow_redirects=True)
    client.post('/login', data={'username': usuario, 'password': password},
                follow_redirects=True)
    return client


@pytest.fixture
def logueado(client):
    return registrar_y_loguear(client, 'usuario4')


def correr(client, **kwargs):
    body = {'key_length': 400, 'engine': 'analytic', 'eve_strategy': 'none'}
    body.update(kwargs)
    return client.post('/api/run-simulation', json=body).get_json()


# ---------------------------------------------------------------- one-time-pad

class TestOneTimePad:

    def test_cifrar_y_descifrar_devuelve_el_original(self):
        clave = '0110100111010010' * 40
        r = otp.cifrar('Hola CONAIISI', clave, 'secure')
        assert r['success'] is True
        assert r['descifrado_por_bob'] == 'Hola CONAIISI'

    def test_el_cifrado_no_es_el_texto_plano(self):
        clave = '1010110100101101' * 40
        r = otp.cifrar('mensaje secreto', clave, 'secure')
        assert r['cifrado_hex'] != 'mensaje secreto'.encode().hex()

    def test_claves_distintas_dan_cifrados_distintos(self):
        a = otp.cifrar('igual', '1010' * 100, 'secure')['cifrado_hex']
        b = otp.cifrar('igual', '0101' * 100, 'secure')['cifrado_hex']
        assert a != b

    def test_soporta_acentos_y_unicode(self):
        clave = '0110100111010010' * 60
        texto = 'canción cuántica ñ'
        r = otp.cifrar(texto, clave, 'secure')
        assert r['descifrado_por_bob'] == texto

    def test_regla_no_cifrar_con_sesion_comprometida(self):
        r = otp.cifrar('hola', '0' * 500, 'compromised')
        assert r['success'] is False
        assert 'comprometida' in r['message'].lower()

    def test_regla_clave_mas_corta_que_el_mensaje(self):
        r = otp.cifrar('un mensaje bastante largo', '0101', 'secure')
        assert r['success'] is False
        assert 'demasiado corta' in r['message']

    def test_mensaje_vacio_rechazado(self):
        assert otp.cifrar('', '0' * 500, 'secure')['success'] is False

    def test_mensaje_demasiado_largo_rechazado(self):
        r = otp.cifrar('x' * 600, '0' * 10000, 'secure')
        assert r['success'] is False
        assert '512' in r['message']

    def test_la_clave_debe_cubrir_8_bits_por_caracter(self):
        # 4 caracteres necesitan 32 bits: con 31 no alcanza, con 32 si
        assert otp.cifrar('abcd', '0' * 31, 'secure')['success'] is False
        assert otp.cifrar('abcd', '0' * 32, 'secure')['success'] is True

    def test_eve_con_clave_parcial_no_recupera_el_mensaje(self):
        clave = '0110100111010010' * 40
        # Eve desconoce la mitad de los bits
        clave_eve = ''.join(c if i % 2 else '?' for i, c in enumerate(clave))
        r = otp.cifrar('mensaje secreto', clave, 'secure', clave_de_eve=clave_eve)
        assert r['descifrado_por_eve'] != 'mensaje secreto'
        assert r['bits_que_eve_desconoce'] > 0


class TestOtpEnLaWeb:

    def test_cifrar_desde_la_vista_de_detalle(self, logueado):
        sid = correr(logueado)['session']['id']
        resp = logueado.post(f'/simulation/{sid}/encrypt',
                             data={'mensaje': 'hola mundo'})
        assert resp.status_code == 200
        assert b'Bob descifra' in resp.data

    def test_no_se_puede_cifrar_con_la_sesion_de_otro(self, client):
        registrar_y_loguear(client, 'duenio')
        sid = correr(client)['session']['id']
        client.get('/logout')

        registrar_y_loguear(client, 'ajeno')
        resp = client.post(f'/simulation/{sid}/encrypt', data={'mensaje': 'x'})
        assert resp.status_code == 404

    def test_sesion_comprometida_no_ofrece_cifrado(self, logueado):
        datos = correr(logueado, key_length=600, noise_rate=40)
        if datos['session']['result'] != 'compromised':
            pytest.skip('la corrida no quedó comprometida')
        sid = datos['session']['id']
        html = logueado.get(f'/simulation/{sid}').data.decode()
        assert 'Esta clave no se puede usar' in html


class TestReconstruccionDeClaveDeEve:

    def test_sin_espia_la_clave_de_eve_es_toda_incognitas(self, logueado):
        traza = correr(logueado, key_length=200, eve_strategy='none')['trace']
        clave = simulation_controller.reconstruir_clave_de_eve(traza)
        assert clave is not None
        assert set(clave) == {'?'}

    def test_con_espia_total_eve_conoce_todos_los_bits(self, logueado):
        traza = correr(logueado, key_length=200,
                       eve_strategy='intercept_resend', eve_fraction=100)['trace']
        clave = simulation_controller.reconstruir_clave_de_eve(traza)
        assert '?' not in clave

    def test_la_clave_de_eve_tiene_el_largo_de_la_clave_final(self, logueado):
        datos = correr(logueado, key_length=200)
        clave_eve = simulation_controller.reconstruir_clave_de_eve(datos['trace'])
        assert len(clave_eve) == datos['session']['final_length']


# ------------------------------------------------------------------- analitica

class TestAnalitica:

    def test_devuelve_las_series(self, logueado):
        for _ in range(3):
            correr(logueado, key_length=200)
        datos = logueado.get('/api/analytics').get_json()

        assert 'histograma' in datos and 'serie' in datos
        assert len(datos['serie']) == 3
        assert sum(datos['histograma']['cuentas']) == 3
        assert datos['umbral'] == 11.0

    def test_el_histograma_ubica_el_qber_en_el_rango_correcto(self, logueado):
        correr(logueado, key_length=600, eve_strategy='intercept_resend',
               eve_fraction=100)
        datos = logueado.get('/api/analytics').get_json()
        # El QBER de un espia total ronda el 25%: nunca en el primer rango
        assert datos['histograma']['cuentas'][0] == 0

    def test_marca_cuales_corridas_tuvieron_espia(self, logueado):
        correr(logueado, eve_strategy='none')
        correr(logueado, eve_strategy='intercept_resend', eve_fraction=100)
        serie = logueado.get('/api/analytics').get_json()['serie']
        assert [p['con_espia'] for p in serie] == [False, True]

    def test_sin_login_no_hay_analitica(self, client):
        assert client.get('/api/analytics').status_code == 302

    def test_no_mezcla_datos_entre_usuarios(self, client):
        registrar_y_loguear(client, 'ana4')
        correr(client)
        correr(client)
        client.get('/logout')

        registrar_y_loguear(client, 'beto4')
        datos = client.get('/api/analytics').get_json()
        assert datos['serie'] == []


# ------------------------------------------------------ gestion de sesiones

class TestBorrado:

    def test_borrar_la_propia_sesion(self, logueado):
        sid = correr(logueado)['session']['id']
        resp = logueado.post(f'/simulation/{sid}/delete', follow_redirects=True)
        assert resp.status_code == 200
        assert logueado.get(f'/simulation/{sid}').status_code == 404

    def test_no_se_puede_borrar_la_sesion_de_otro(self, client, app):
        from datos import session_repository

        registrar_y_loguear(client, 'victima')
        sid = correr(client)['session']['id']
        client.get('/logout')

        registrar_y_loguear(client, 'atacante')
        client.post(f'/simulation/{sid}/delete', follow_redirects=True)

        with app.app_context():
            assert session_repository.get_session_by_id(sid) is not None, \
                'FUGA: se borró la sesión de otro usuario'

    def test_el_controller_valida_la_propiedad(self, logueado, app):
        sid = correr(logueado)['session']['id']
        with app.app_context():
            assert simulation_controller.delete_user_session(sid, 999) is False
            assert simulation_controller.delete_user_session(sid, 1) is True


class TestPaginacion:

    def test_pagina_los_resultados(self, logueado, app):
        for _ in range(7):
            correr(logueado, key_length=50)

        with app.app_context():
            p1 = simulation_controller.get_paginated_history(1, pagina=1, por_pagina=3)
            assert len(p1['sesiones']) == 3
            assert p1['total'] == 7
            assert p1['total_paginas'] == 3
            assert p1['hay_anterior'] is False
            assert p1['hay_siguiente'] is True

            p3 = simulation_controller.get_paginated_history(1, pagina=3, por_pagina=3)
            assert len(p3['sesiones']) == 1
            assert p3['hay_siguiente'] is False

    def test_no_repite_filas_entre_paginas(self, logueado, app):
        for _ in range(6):
            correr(logueado, key_length=50)
        with app.app_context():
            a = simulation_controller.get_paginated_history(1, pagina=1, por_pagina=3)
            b = simulation_controller.get_paginated_history(1, pagina=2, por_pagina=3)
        ids_a = {s['id'] for s in a['sesiones']}
        ids_b = {s['id'] for s in b['sesiones']}
        assert not (ids_a & ids_b), 'hay filas repetidas entre páginas'

    def test_pagina_fuera_de_rango_se_acota(self, logueado, app):
        correr(logueado, key_length=50)
        with app.app_context():
            r = simulation_controller.get_paginated_history(1, pagina=999)
            assert r['pagina'] == r['total_paginas']

    def test_pagina_invalida_no_rompe(self, logueado):
        assert logueado.get('/history?pagina=0').status_code == 200
        assert logueado.get('/history?pagina=abc').status_code == 200
        assert logueado.get('/history?pagina=-5').status_code == 200


class TestExportacion:

    def test_exporta_json_descargable(self, logueado):
        sid = correr(logueado, key_length=100)['session']['id']
        resp = logueado.get(f'/simulation/{sid}/export')

        assert resp.status_code == 200
        assert 'attachment' in resp.headers['Content-Disposition']
        assert f'simulacion-{sid}.json' in resp.headers['Content-Disposition']

        datos = json.loads(resp.data)
        assert datos['session']['id'] == sid
        assert datos['trace'] is not None

    def test_no_se_exporta_la_sesion_de_otro(self, client):
        registrar_y_loguear(client, 'duenio2')
        sid = correr(client)['session']['id']
        client.get('/logout')

        registrar_y_loguear(client, 'ajeno2')
        assert client.get(f'/simulation/{sid}/export').status_code == 404
