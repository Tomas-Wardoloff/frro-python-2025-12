"""
Tests de navegador con Playwright.

Cubren lo único que ninguna otra suite puede verificar: el JavaScript. Todos
los demás tests llegan hasta el HTML que sale del servidor, así que un error en
el navegador —la animación, los gráficos, el cálculo del QBER previsto— pasaría
desapercibido.

El test central es ``test_los_bits_en_pantalla_son_los_del_backend``: durante
mucho tiempo la animación generó los bits con ``Math.random()`` en el browser,
de modo que lo que se veía no tenía relación con la simulación que corría el
servidor. Este test intercepta la respuesta de la API y compara, bit por bit,
contra lo que efectivamente quedó dibujado.

Requiere Playwright y Chromium:

    pip install -r requirements-dev.txt
    playwright install chromium

Si no están instalados, los tests se saltean con un aviso.
"""
import json
import socket
import threading
import time

import pytest

pytest.importorskip('playwright', reason='Playwright no está instalado')

# Todos los tests de este archivo manejan un navegador real
pytestmark = pytest.mark.browser

from playwright.sync_api import sync_playwright  # noqa: E402

from app import create_app  # noqa: E402
from config import TestingConfig  # noqa: E402


def esperar_fin_de_animacion(pagina, timeout=45000):
    """Espera a que la animación termine de verdad.

    Se espera el texto de estado y no sólo la aparición del botón: el botón
    llegó a estar visible desde el arranque por un choque de CSS, y los tests
    leían el DOM a mitad de la animación.
    """
    pagina.wait_for_selector('text=Simulación completada.', timeout=timeout)
    pagina.wait_for_selector('#dashboard-button', state='visible', timeout=5000)


def _puerto_libre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='module')
def servidor(tmp_path_factory):
    """Levanta la app en un hilo aparte y devuelve su URL base."""
    import os

    ruta = tmp_path_factory.mktemp('nav') / 'nav.db'

    class Cfg(TestingConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{ruta}'

    aplicacion = create_app(Cfg)
    puerto = _puerto_libre()

    hilo = threading.Thread(
        target=lambda: aplicacion.run(port=puerto, use_reloader=False, threaded=True),
        daemon=True,
    )
    hilo.start()

    # Esperar a que responda
    base = f'http://127.0.0.1:{puerto}'
    import urllib.error
    import urllib.request
    for _ in range(50):
        try:
            urllib.request.urlopen(base, timeout=1)
            break
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    else:
        pytest.fail('el servidor de prueba no respondió')

    yield base

    if os.path.exists(ruta):
        os.remove(ruta)


@pytest.fixture(scope='module')
def navegador():
    with sync_playwright() as p:
        nav = p.chromium.launch()
        yield nav
        nav.close()


@pytest.fixture
def pagina(navegador, servidor):
    """Página con un usuario ya registrado y con sesión iniciada."""
    contexto = navegador.new_context()
    pag = contexto.new_page()

    usuario = f'nav{int(time.time() * 1000) % 1000000}'

    pag.goto(f'{servidor}/register')
    pag.fill('#username', usuario)
    pag.fill('#password', 'password123')
    pag.click('#submit')

    pag.wait_for_url('**/login')
    pag.fill('#username', usuario)
    pag.fill('#password', 'password123')
    pag.click('#submit')
    pag.wait_for_url('**/dashboard')

    yield pag
    contexto.close()


# ============================================================ la animación

class TestAnimacion:

    def test_los_bits_en_pantalla_son_los_del_backend(self, pagina, servidor):
        """El test que cierra el agujero: lo dibujado == lo simulado.

        La animación llegó a generar los bits con Math.random(), con lo cual
        mostraba datos sin relación con la corrida real.
        """
        respuesta = {}

        def capturar(response):
            if 'run-simulation' in response.url:
                respuesta['datos'] = response.json()

        pagina.on('response', capturar)

        pagina.goto(f'{servidor}/animation?key_length=300&eve_strategy=none&engine=analytic')
        # La animación dibuja de a un bit con pausas; se espera al botón final
        esperar_fin_de_animacion(pagina)

        assert 'datos' in respuesta, 'la página nunca llamó a la API'
        traza = respuesta['datos']['trace']

        # Bits de Alice dibujados
        alice = pagina.eval_on_selector_all(
            '#alice-bits-display .bit-square',
            'nodos => nodos.map(n => n.textContent.trim())'
        )
        assert alice, 'no se dibujó ningún bit de Alice'
        esperados = [str(b) for b in traza['alice_bits'][:len(alice)]]
        assert alice == esperados, (
            f'la pantalla muestra {alice} pero el backend envió {esperados}'
        )

        # Mediciones de Bob dibujadas
        bob = pagina.eval_on_selector_all(
            '#bob-bits-display .bit-square',
            'nodos => nodos.map(n => n.textContent.trim())'
        )
        assert bob == [str(b) for b in traza['bob_results'][:len(bob)]]

    def test_los_bits_de_eve_tambien_son_reales(self, pagina, servidor):
        """Donde Eve no interceptó tiene que verse un hueco, no un bit inventado."""
        respuesta = {}
        pagina.on('response', lambda r: respuesta.update(
            {'datos': r.json()} if 'run-simulation' in r.url else {}))

        pagina.goto(f'{servidor}/animation'
                    '?key_length=300&eve_strategy=intercept_resend&eve_fraction=50&engine=analytic')
        esperar_fin_de_animacion(pagina)

        traza = respuesta['datos']['trace']
        celdas = pagina.eval_on_selector_all(
            '#eve-bits-display .bit-square',
            'nodos => nodos.map(n => n.textContent.trim())'
        )
        assert celdas, 'no se dibujaron los bits de Eve'

        for i, celda in enumerate(celdas):
            bit = traza['eve_bits'][i]
            if bit < 0:
                assert celda == '·', f'qubit {i}: Eve no lo tocó pero se muestra {celda!r}'
            else:
                assert celda == str(bit), f'qubit {i}: muestra {celda!r}, real {bit}'

    def test_sin_espia_no_se_muestra_la_seccion_de_eve(self, pagina, servidor):
        pagina.goto(f'{servidor}/animation?key_length=200&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)
        assert not pagina.is_visible('#eve-section')

    def test_el_qber_mostrado_coincide_con_el_calculado(self, pagina, servidor):
        respuesta = {}
        pagina.on('response', lambda r: respuesta.update(
            {'datos': r.json()} if 'run-simulation' in r.url else {}))

        pagina.goto(f'{servidor}/animation?key_length=400&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)

        real = respuesta['datos']['session']['error_rate'] * 100
        texto = pagina.inner_text('#qber-result')
        assert f'{real:.2f}%' in texto, f'la pantalla dice {texto!r}, el backend {real:.2f}%'

    def test_la_clave_final_mostrada_es_la_generada(self, pagina, servidor):
        respuesta = {}
        pagina.on('response', lambda r: respuesta.update(
            {'datos': r.json()} if 'run-simulation' in r.url else {}))

        pagina.goto(f'{servidor}/animation?key_length=400&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)

        clave = respuesta['datos']['session']['final_key']
        mostrada = pagina.inner_text('#final-key-text')
        assert clave.startswith(mostrada.replace('...', ''))

    def test_no_quedan_errores_de_javascript(self, pagina, servidor):
        errores = []
        pagina.on('pageerror', lambda e: errores.append(str(e)))
        pagina.on('console', lambda m: errores.append(m.text) if m.type == 'error' else None)

        pagina.goto(f'{servidor}/animation?key_length=200&eve_strategy=intercept_resend'
                    '&eve_fraction=100&engine=analytic')
        esperar_fin_de_animacion(pagina)

        assert not errores, f'errores de JS en la animación: {errores}'


# ======================================================== el formulario

class TestFormularioDelSimulador:

    def test_el_qber_previsto_se_actualiza_con_los_controles(self, pagina, servidor):
        pagina.goto(f'{servidor}/simulator')

        # Sin espía ni ruido: 0%
        assert pagina.inner_text('#qber-preview').startswith('0.0')
        assert 'Clave segura' in pagina.inner_text('#qber-verdict')

        # Con espía interceptando todo: ~25%, por encima del umbral
        pagina.select_option('#eve-strategy', 'intercept_resend')
        pagina.fill('#fraction-range', '100')
        pagina.dispatch_event('#fraction-range', 'input')

        assert pagina.inner_text('#qber-preview').startswith('25.0')
        assert 'descartada' in pagina.inner_text('#qber-verdict')

    def test_el_ruido_solo_ya_puede_superar_el_umbral(self, pagina, servidor):
        """Lo que mejor se muestra en vivo: sin espía, pero clave descartada."""
        pagina.goto(f'{servidor}/simulator')
        pagina.fill('#noise-range', '20')
        pagina.dispatch_event('#noise-range', 'input')

        assert pagina.inner_text('#qber-preview').startswith('20.0')
        assert 'descartada' in pagina.inner_text('#qber-verdict')
        # Y sin ningún espía configurado
        assert pagina.input_value('#eve-strategy') == 'none'

    def test_la_fraccion_se_oculta_cuando_no_hay_espia(self, pagina, servidor):
        pagina.goto(f'{servidor}/simulator')
        assert not pagina.is_visible('#eve-fraction-group')

        pagina.select_option('#eve-strategy', 'intercept_resend')
        assert pagina.is_visible('#eve-fraction-group')

    def test_el_formulario_lleva_a_la_animacion(self, pagina, servidor):
        pagina.goto(f'{servidor}/simulator')
        pagina.fill('#key_length', '250')
        pagina.fill('#noise-range', '5')
        pagina.dispatch_event('#noise-range', 'input')
        pagina.click('#submit')

        pagina.wait_for_url('**/animation*')
        assert 'key_length=250' in pagina.url
        assert 'noise_rate=5' in pagina.url


# ============================================================ el dashboard

class TestGraficos:

    def test_los_graficos_se_dibujan(self, pagina, servidor):
        # Primero hace falta al menos una simulación
        pagina.goto(f'{servidor}/animation?key_length=200&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)

        pagina.goto(f'{servidor}/dashboard')
        pagina.wait_for_selector('#graficos-seccion', state='visible', timeout=15000)

        # Chart.js registra sus instancias; si no se creó, no hay grafico
        for canvas in ('grafico-histograma', 'grafico-serie'):
            creado = pagina.evaluate(
                f"() => !!Chart.getChart(document.getElementById('{canvas}'))"
            )
            assert creado, f'{canvas} no se dibujó'

    def test_el_dashboard_no_tira_errores_de_javascript(self, pagina, servidor):
        errores = []
        pagina.on('pageerror', lambda e: errores.append(str(e)))

        pagina.goto(f'{servidor}/animation?key_length=200&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)
        pagina.goto(f'{servidor}/dashboard')
        pagina.wait_for_timeout(1500)

        assert not errores, f'errores de JS en el dashboard: {errores}'


# ====================================================== recorrido completo

class TestRecorridoEnNavegador:

    def test_de_la_configuracion_al_mensaje_cifrado(self, pagina, servidor):
        """El recorrido que haría alguien en la demo, con el browser de verdad."""
        # Configurar
        pagina.goto(f'{servidor}/simulator')
        pagina.fill('#key_length', '800')
        pagina.click('#submit')

        # Ver la animación
        pagina.wait_for_url('**/animation*')
        esperar_fin_de_animacion(pagina)

        # Ir al detalle
        pagina.click('#detail-link')
        pagina.wait_for_selector('text=Traza del protocolo', timeout=15000)
        assert pagina.is_visible('text=Base Alice')

        # Cifrar un mensaje
        pagina.fill('#mensaje', 'hola congreso')
        pagina.click('button:has-text("Cifrar")')
        pagina.wait_for_selector('text=Bob descifra', timeout=15000)

        assert pagina.is_visible('text=hola congreso')
        assert pagina.is_visible('text=Eve intenta descifrar')


class TestVisibilidadDeControles:
    """Los botones del final no pueden estar visibles durante la animación."""

    def test_los_botones_aparecen_recien_al_terminar(self, pagina, servidor):
        """La clase d-flex de Bootstrap es display:flex !important y le ganaba
        al display:none inline, con lo que los botones se veían desde el
        arranque."""
        pagina.goto(f'{servidor}/animation?key_length=600&eve_strategy=none&engine=analytic')

        # Apenas carga, con la animación todavía corriendo
        pagina.wait_for_selector('#alice-bits-display .bit-square', timeout=15000)
        assert not pagina.is_visible('#dashboard-button'), (
            'los botones del final se ven durante la animación'
        )

        esperar_fin_de_animacion(pagina)
        assert pagina.is_visible('#dashboard-button')


# ============================================================== responsive

VIEWPORTS_MOVILES = [
    ('iPhone SE', 375, 667),
    ('iPhone 14', 390, 844),
    ('iPad mini', 768, 1024),
]

_JS_ANCHO = "() => document.documentElement.scrollWidth"

_JS_DESBORDES = """(vw) => {
    const malos = [];
    document.querySelectorAll('*').forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.right > vw + 2 && r.width > 0) {
            const cls = String(el.className || '').split(' ').slice(0, 2).join('.');
            malos.push(el.tagName.toLowerCase() + (cls ? '.' + cls : ''));
        }
    });
    return [...new Set(malos)].slice(0, 5);
}"""


def _ancho_del_documento(pagina):
    return pagina.evaluate(_JS_ANCHO)


def _ancho_estable(pagina, intentos=12, pausa=250):
    """Mide el ancho del documento hasta que deja de cambiar.

    Con una espera fija la medicion puede caer mientras Chart.js todavia
    redimensiona sus canvas o las fuentes siguen cargando, y el ancho reportado
    es momentaneamente mayor que el definitivo. Eso hacia fallar estos tests al
    azar. Se espera a que dos lecturas seguidas coincidan.
    """
    pagina.wait_for_load_state('networkidle')
    anterior = None
    for _ in range(intentos):
        actual = _ancho_del_documento(pagina)
        if actual == anterior:
            return actual
        anterior = actual
        pagina.wait_for_timeout(pausa)
    return anterior


def _elementos_que_desbordan(pagina, ancho):
    """Los elementos que se salen del viewport, para poder arreglarlos."""
    return pagina.evaluate(_JS_DESBORDES, ancho)


class TestResponsive:
    """El sitio tiene que verse bien en celular.

    El checklist del TPI lo pide, y en la demo alguien va a abrir la URL en el
    telefono. El defecto clasico es el desborde horizontal: contenido mas ancho
    que la pantalla, que obliga a hacer scroll lateral. Las tablas anchas -la
    traza tiene siete columnas- son las candidatas naturales.
    """

    @pytest.mark.parametrize('dispositivo,ancho,alto', VIEWPORTS_MOVILES)
    def test_las_paginas_publicas_no_desbordan(self, navegador, servidor,
                                               dispositivo, ancho, alto):
        contexto = navegador.new_context(viewport={'width': ancho, 'height': alto})
        pag = contexto.new_page()
        try:
            for ruta in ('/', '/login', '/register'):
                pag.goto(f'{servidor}{ruta}')
                doc = _ancho_estable(pag)
                assert doc <= ancho + 2, (
                    f'{ruta} en {dispositivo}: el documento mide {doc}px sobre '
                    f'{ancho}px. Desbordan: {_elementos_que_desbordan(pag, ancho)}'
                )
        finally:
            contexto.close()

    @pytest.mark.parametrize('dispositivo,ancho,alto', VIEWPORTS_MOVILES)
    def test_las_paginas_privadas_no_desbordan(self, pagina, servidor,
                                               dispositivo, ancho, alto):
        # Una corrida para que el historial y el detalle tengan contenido
        pagina.goto(f'{servidor}/animation?key_length=600'
                    '&eve_strategy=intercept_resend&eve_fraction=60&engine=analytic')
        esperar_fin_de_animacion(pagina)
        sid = pagina.get_attribute('#detail-link', 'href').rstrip('/').split('/')[-1]

        pagina.set_viewport_size({'width': ancho, 'height': alto})

        for nombre, ruta in (('simulador', '/simulator'), ('dashboard', '/dashboard'),
                             ('historial', '/history'), ('detalle', f'/simulation/{sid}')):
            pagina.goto(f'{servidor}{ruta}')
            doc = _ancho_estable(pagina)
            assert doc <= ancho + 2, (
                f'{nombre} en {dispositivo}: el documento mide {doc}px sobre '
                f'{ancho}px. Desbordan: {_elementos_que_desbordan(pagina, ancho)}'
            )

    def test_la_tabla_de_la_traza_scrollea_dentro_de_su_caja(self, pagina, servidor):
        """La tabla es ancha a proposito; lo que no puede es empujar la pagina."""
        pagina.goto(f'{servidor}/animation?key_length=400&eve_strategy=none&engine=analytic')
        esperar_fin_de_animacion(pagina)
        pagina.click('#detail-link')
        pagina.wait_for_selector('text=Traza del protocolo', timeout=15000)

        pagina.set_viewport_size({'width': 375, 'height': 667})
        pagina.wait_for_timeout(400)

        contenedor = pagina.evaluate(
            "() => { const t = document.querySelector('.table-responsive');"
            " return t ? {scroll: t.scrollWidth, visible: t.clientWidth} : null; }"
        )
        assert contenedor, 'la tabla no esta en un contenedor scrolleable'
        assert _ancho_estable(pagina) <= 377, 'la tabla empuja la pagina'
