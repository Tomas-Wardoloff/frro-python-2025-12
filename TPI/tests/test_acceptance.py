"""
Tests de aceptación: recorridos completos de usuario.

A diferencia de los tests unitarios, que verifican piezas sueltas, estos
recorren el sistema como lo haría una persona: registrarse, entrar, configurar
una simulación, verla correr, revisar el detalle y cifrar un mensaje.

Existen para que el CI detecte una regresión que rompa el flujo aunque cada
pieza pase sus tests por separado.
"""
import json

import pytest


# --------------------------------------------------------------- utilidades

def registrarse(client, usuario, password='password123'):
    return client.post('/register',
                       data={'username': usuario, 'password': password},
                       follow_redirects=True)


def entrar(client, usuario, password='password123'):
    return client.post('/login',
                       data={'username': usuario, 'password': password},
                       follow_redirects=True)


def configurar_simulacion(client, **campos):
    """Manda el formulario del simulador y devuelve la URL de la animación."""
    datos = {
        'key_length': 300, 'noise_rate': 0,
        'eve_strategy': 'none', 'eve_fraction': 0, 'engine': 'analytic',
    }
    datos.update(campos)
    resp = client.post('/simulator', data=datos)
    assert resp.status_code == 302, 'el formulario no redirigió a la animación'
    return resp.headers['Location']


def ejecutar(client, **params):
    """Ejecuta la simulación como lo hace el JavaScript de la animación."""
    cuerpo = {
        'key_length': 300, 'noise_rate': 0,
        'eve_strategy': 'none', 'eve_fraction': 0, 'engine': 'analytic',
    }
    cuerpo.update(params)
    resp = client.post('/api/run-simulation', json=cuerpo)
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()


# ------------------------------------------------------------- recorridos

class TestRecorridoClaveSegura:
    """Un usuario nuevo genera una clave y cifra un mensaje con ella."""

    def test_de_registro_a_mensaje_cifrado(self, client):
        # 1. Se registra y entra
        assert b'exitosamente' in registrarse(client, 'alicia').data
        assert b'Dashboard' in entrar(client, 'alicia').data

        # 2. El dashboard arranca vacío
        assert client.get('/dashboard').status_code == 200

        # 3. Configura una simulación sin espía ni ruido.
        #    800 qubits dejan ~380 bits de clave, suficientes para el mensaje
        #    que se cifra abajo (el one-time-pad gasta 8 bits por carácter).
        destino = configurar_simulacion(client, key_length=800)
        assert 'key_length=800' in destino
        assert client.get(destino).status_code == 200

        # 4. La animación ejecuta la simulación
        datos = ejecutar(client, key_length=800)
        assert datos['session']['result'] == 'secure'
        clave = datos['session']['final_key']
        assert clave, 'una corrida limpia tiene que producir clave'

        # 5. La traza que recibe la animación es real
        traza = datos['trace']
        assert len(traza['alice_bits']) == 256  # recortada
        for i in traza['sifted_indices']:
            assert traza['bob_results'][i] == traza['alice_bits'][i]

        # 6. Aparece en el historial
        sid = datos['session']['id']
        assert f'/simulation/{sid}'.encode() in client.get('/history').data

        # 7. El detalle muestra el protocolo
        detalle = client.get(f'/simulation/{sid}')
        assert detalle.status_code == 200
        assert b'Base Alice' in detalle.data

        # 8. Cifra un mensaje con la clave
        cifrado = client.post(f'/simulation/{sid}/encrypt',
                              data={'mensaje': 'nos vemos en el congreso'})
        assert cifrado.status_code == 200
        assert b'Bob descifra' in cifrado.data
        assert 'nos vemos en el congreso'.encode() in cifrado.data

        # 9. Exporta la simulación
        exportado = json.loads(client.get(f'/simulation/{sid}/export').data)
        assert exportado['session']['final_key'] == clave
        assert exportado['trace'] is not None

        # 10. La borra
        client.post(f'/simulation/{sid}/delete', follow_redirects=True)
        assert client.get(f'/simulation/{sid}').status_code == 404


class TestRecorridoEspiaDetectado:
    """Un espía interceptando todo se detecta y la clave se descarta."""

    def test_el_espia_deja_la_clave_inutilizable(self, client):
        registrarse(client, 'beto')
        entrar(client, 'beto')

        # Se buscan varias corridas: la detección es probabilística
        comprometida = None
        for _ in range(15):
            datos = ejecutar(client, key_length=500,
                             eve_strategy='intercept_resend', eve_fraction=100)
            if datos['session']['result'] == 'compromised':
                comprometida = datos
                break

        assert comprometida, 'un espía total debería detectarse en 15 intentos'
        assert comprometida['session']['final_key'] is None

        # La vista de detalle no ofrece cifrar con una clave comprometida
        sid = comprometida['session']['id']
        html = client.get(f'/simulation/{sid}').data.decode()
        assert 'Esta clave no se puede usar' in html

        # Y si se intenta igual, la capa de negocio lo rechaza
        resp = client.post(f'/simulation/{sid}/encrypt', data={'mensaje': 'hola'})
        assert 'Esta clave no se puede usar' in resp.data.decode()

        # La traza muestra que Eve tocó todos los qubits
        assert all(comprometida['trace']['intercepted'])


class TestRecorridoCanalRuidoso:
    """Un canal muy ruidoso inutiliza el enlace aunque no haya espía."""

    def test_el_ruido_solo_descarta_la_clave(self, client):
        registrarse(client, 'carla')
        entrar(client, 'carla')

        descartada = None
        for _ in range(10):
            datos = ejecutar(client, key_length=600, noise_rate=35,
                             eve_strategy='none')
            if datos['session']['result'] == 'compromised':
                descartada = datos
                break

        assert descartada, 'con 35% de ruido la clave debería descartarse'
        # El diagnóstico tiene que atribuirlo al ruido y no a un intruso
        assert 'ruido' in descartada['message'].lower()
        # Y efectivamente no hubo espía
        assert not any(descartada['trace']['intercepted'])


class TestRecorridoDosUsuarios:
    """Los datos de un usuario no son accesibles para otro."""

    def test_las_simulaciones_no_se_filtran(self, client):
        registrarse(client, 'duenia')
        entrar(client, 'duenia')
        sid = ejecutar(client)['session']['id']
        client.get('/logout')

        registrarse(client, 'ajeno')
        entrar(client, 'ajeno')

        # Ni ver, ni exportar, ni cifrar, ni borrar
        assert client.get(f'/simulation/{sid}').status_code == 404
        assert client.get(f'/simulation/{sid}/export').status_code == 404
        assert client.post(f'/simulation/{sid}/encrypt',
                           data={'mensaje': 'x'}).status_code == 404
        client.post(f'/simulation/{sid}/delete', follow_redirects=True)

        # El historial del segundo usuario sigue vacío
        assert b'Comprometida' not in client.get('/history').data

        # Y la sesión del primero sigue existiendo
        client.get('/logout')
        entrar(client, 'duenia')
        assert client.get(f'/simulation/{sid}').status_code == 200


class TestRecorridoAnalitica:
    """El dashboard refleja lo que el usuario fue corriendo."""

    def test_los_graficos_reflejan_las_corridas(self, client):
        registrarse(client, 'dani')
        entrar(client, 'dani')

        ejecutar(client, eve_strategy='none')
        ejecutar(client, eve_strategy='intercept_resend', eve_fraction=100)
        ejecutar(client, eve_strategy='none')

        datos = client.get('/api/analytics').get_json()
        assert len(datos['serie']) == 3
        assert sum(datos['histograma']['cuentas']) == 3
        assert [p['con_espia'] for p in datos['serie']] == [False, True, False]

        stats = client.get('/dashboard')
        assert stats.status_code == 200
        assert b'Total Simulaciones' in stats.data


class TestAmbosMotores:
    """La aplicación funciona igual con cualquiera de los dos motores."""

    @pytest.mark.parametrize('motor', ['analytic', 'qiskit'])
    def test_el_recorrido_funciona_con_cada_motor(self, client, motor):
        registrarse(client, f'motor_{motor}')
        entrar(client, f'motor_{motor}')

        datos = ejecutar(client, key_length=200, engine=motor)
        assert datos['success'] is True
        assert datos['session']['result'] == 'secure'

        sid = datos['session']['id']
        assert client.get(f'/simulation/{sid}').status_code == 200


class TestRecorridoClaveInsuficiente:
    """El one-time-pad exige una clave al menos tan larga como el mensaje."""

    def test_avisa_cuando_la_clave_no_alcanza(self, client):
        """Una corrida corta produce una clave que no cubre un mensaje largo.

        Es la restricción propia del one-time-pad, no un defecto: estirar o
        reutilizar la clave rompería su garantía. El sistema tiene que
        explicarlo en vez de cifrar mal.
        """
        registrarse(client, 'corta')
        entrar(client, 'corta')

        datos = ejecutar(client, key_length=200)
        clave = datos['session']['final_key']
        sid = datos['session']['id']

        # Un mensaje que necesita más bits de los que hay
        mensaje = 'x' * (len(clave) // 8 + 20)
        resp = client.post(f'/simulation/{sid}/encrypt', data={'mensaje': mensaje})

        assert resp.status_code == 200
        assert 'demasiado corta' in resp.data.decode()
        assert b'Bob descifra' not in resp.data

    def test_la_vista_informa_cuantos_caracteres_entran(self, client):
        registrarse(client, 'informada')
        entrar(client, 'informada')

        datos = ejecutar(client, key_length=400)
        sid = datos['session']['id']
        capacidad = len(datos['session']['final_key']) // 8

        html = client.get(f'/simulation/{sid}').data.decode()
        assert f'alcanza\n                        para {capacidad} caracteres' in html \
            or f'para {capacidad} caracteres' in html
