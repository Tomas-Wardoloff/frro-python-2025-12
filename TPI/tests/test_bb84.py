"""
Tests del protocolo BB84.

A diferencia de la versión anterior, estos tests **no** se auto-saltean si algo
falla al importar: una rotura real de la capa de simulación tiene que poner el
build en rojo, no en verde.
"""
import pytest

from business.bb84 import UMBRAL_QBER, simulate_bb84
from business.bb84.protocol import MIN_BITS_CRIBADOS


class TestEstructuraDelProtocolo:
    """La simulación devuelve una traza coherente."""

    def test_devuelve_traza_completa(self):
        r = simulate_bb84(128, has_eve=False, seed=1)

        assert r.success
        assert len(r.alice_bits) == 128
        assert len(r.alice_bases) == 128
        assert len(r.bob_bases) == 128
        assert len(r.bob_results) == 128
        assert all(b in (0, 1) for b in r.alice_bits)
        assert all(b in (0, 1) for b in r.bob_bases)

    def test_bases_coincidentes_son_las_cribadas(self):
        r = simulate_bb84(200, has_eve=False, seed=7)

        esperadas = [
            i for i in range(200)
            if r.alice_bases[i] == r.bob_bases[i]
        ]
        assert r.sifted_indices == esperadas

    def test_sin_eve_ni_ruido_bob_reproduce_los_bits_cribados(self):
        """Sin perturbación, Bob mide exactamente lo que envió Alice."""
        r = simulate_bb84(300, has_eve=False, seed=3)

        for i in r.sifted_indices:
            assert r.bob_results[i] == r.alice_bits[i]

    def test_la_semilla_hace_la_corrida_reproducible(self):
        a = simulate_bb84(64, has_eve=True, seed=42)
        b = simulate_bb84(64, has_eve=True, seed=42)

        assert a.alice_bits == b.alice_bits
        assert a.bob_results == b.bob_results
        assert a.error_rate == b.error_rate


class TestReglaDeNegocioQBER:
    """Regla de negocio: la clave se descarta si el QBER supera el umbral."""

    def test_sin_espia_la_clave_es_segura(self):
        r = simulate_bb84(256, has_eve=False, seed=11)

        assert r.result == 'secure'
        assert r.error_rate < UMBRAL_QBER
        assert r.final_key is not None

    def test_espia_total_compromete_la_clave_casi_siempre(self):
        """Interceptación completa deja el QBER cerca del 25%, muy sobre el umbral.

        La detección es probabilística, no certeza: el QBER se estima sobre una
        muestra de a lo sumo 20 bits, así que de vez en cuando la muestra no
        delata a Eve. Es una propiedad real del protocolo (la probabilidad de
        que se escape cae exponencialmente con el tamaño de la muestra), no un
        defecto de la implementación.
        """
        corridas = 50
        resultados = [simulate_bb84(256, has_eve=True, seed=s) for s in range(corridas)]

        # El QBER medio tiene que rondar el 25% teórico del intercept-resend
        qber_medio = sum(r.error_rate for r in resultados) / corridas
        assert 0.20 < qber_medio < 0.30

        # Con muestras de 20 bits, la teoría da ~91% de detección
        # (P(X<=2) con X~Binomial(20, 0.25) ~= 9% de escape). Se exige 80%
        # para dejar margen y que el test no dependa de la suerte del muestreo.
        comprometidas = sum(r.result == 'compromised' for r in resultados)
        assert comprometidas >= corridas * 0.8

    def test_clave_comprometida_no_se_entrega(self):
        r = simulate_bb84(256, has_eve=True, seed=5)

        assert r.result == 'compromised'
        assert r.final_key is None

    def test_los_bits_revelados_no_quedan_en_la_clave(self):
        r = simulate_bb84(256, has_eve=False, seed=9)

        assert r.final_length == r.sifted_length - len(r.sample_indices)


class TestRegresionClaveCorta:
    """B1: con pocas bases coincidentes el cálculo del QBER dividía por cero."""

    def test_key_length_minimo_nunca_explota(self):
        """El mínimo que acepta el formulario fallaba ~20% de las veces."""
        for semilla in range(200):
            r = simulate_bb84(10, has_eve=False, seed=semilla)
            # Puede abortar por falta de bases coincidentes, pero nunca romper
            assert r.success or r.result == 'aborted'

    def test_aborta_con_mensaje_util_si_no_alcanzan_las_bases(self):
        abortadas = [
            r for r in (
                simulate_bb84(10, has_eve=False, seed=s) for s in range(200)
            )
            if not r.success
        ]
        assert abortadas, 'se esperaba al menos una corrida abortada con n=10'
        for r in abortadas:
            assert r.sifted_length < MIN_BITS_CRIBADOS
            assert 'bases' in r.message.lower()

    @pytest.mark.parametrize('n', [10, 11, 12, 16, 32])
    def test_longitudes_chicas_no_rompen(self, n):
        for semilla in range(50):
            simulate_bb84(n, has_eve=True, seed=semilla)
