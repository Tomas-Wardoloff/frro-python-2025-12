"""
Validación cruzada de los motores de simulación.

El motor analítico resuelve el canal BB84 en forma cerrada; el de Qiskit lo
simula con circuitos cuánticos reales. Si ambos coinciden con la predicción
teórica del QBER, el modelo analítico queda validado contra un simulador
cuántico y se lo puede usar como motor por defecto sin perder fidelidad.

Es lo que permite deployar sin arrastrar Qiskit + SciPy (~130 MB).
"""
import pytest

from business.bb84 import MOTOR_ANALITICO, MOTOR_QISKIT, qber_esperado, simulate_bb84
from business.bb84.engines import qiskit_engine

# Escenarios (ruido del canal, fracción interceptada por Eve)
ESCENARIOS = [
    (0.00, 0.00),   # canal ideal
    (0.00, 1.00),   # espía interceptando todo
    (0.00, 0.50),   # espía interceptando la mitad
    (0.05, 0.00),   # canal ruidoso sin espía
    (0.03, 0.40),   # ruido y espía combinados
]

# Bits por escenario. Con 4000 qubits quedan ~2000 cribados, con lo que el
# error estándar del QBER medido es de ~0.010 en el peor caso (p=0.25).
N_BITS = 4000

# 4 desviaciones estándar. La tolerancia anterior de 0.03 quedaba a 3.1 sigma
# y hacía fallar la suite cada tantas corridas: no por un problema del motor,
# sino porque comparar una medición estadística contra la teoría con un margen
# tan justo falla por definición una fracción de las veces.
TOLERANCIA = 0.04

requiere_qiskit = pytest.mark.skipif(
    not qiskit_engine.disponible(),
    reason='Qiskit no está instalado en este entorno'
)


def _qber_medido(motor, noise_rate, eve_fraction, seed):
    """QBER real sobre TODOS los bits cribados (no sobre la muestra de 20)."""
    r = simulate_bb84(
        N_BITS,
        noise_rate=noise_rate,
        eve_strategy='intercept_resend' if eve_fraction else 'none',
        eve_fraction=eve_fraction,
        engine=motor,
        seed=seed,
    )
    errores = sum(
        1 for i in r.sifted_indices if r.alice_bits[i] != r.bob_results[i]
    )
    return errores / len(r.sifted_indices)


class TestMotorAnaliticoContraTeoria:
    """El motor analítico reproduce el QBER teórico."""

    @pytest.mark.parametrize('noise_rate,eve_fraction', ESCENARIOS)
    def test_qber_coincide_con_la_teoria(self, noise_rate, eve_fraction):
        medido = _qber_medido(MOTOR_ANALITICO, noise_rate, eve_fraction, seed=1)
        teorico = qber_esperado(noise_rate, eve_fraction)

        assert abs(medido - teorico) < TOLERANCIA, (
            f'ruido={noise_rate} eve={eve_fraction}: '
            f'medido {medido:.4f} vs teórico {teorico:.4f}'
        )


@requiere_qiskit
class TestMotorQiskitContraTeoria:
    """El motor de circuitos cuánticos reproduce el mismo QBER teórico."""

    @pytest.mark.parametrize('noise_rate,eve_fraction', ESCENARIOS)
    def test_qber_coincide_con_la_teoria(self, noise_rate, eve_fraction):
        medido = _qber_medido(MOTOR_QISKIT, noise_rate, eve_fraction, seed=1)
        teorico = qber_esperado(noise_rate, eve_fraction)

        assert abs(medido - teorico) < TOLERANCIA, (
            f'ruido={noise_rate} eve={eve_fraction}: '
            f'medido {medido:.4f} vs teórico {teorico:.4f}'
        )


@requiere_qiskit
class TestEquivalenciaEntreMotores:
    """Los dos motores describen el mismo canal físico."""

    @pytest.mark.parametrize('noise_rate,eve_fraction', ESCENARIOS)
    def test_ambos_motores_dan_el_mismo_qber(self, noise_rate, eve_fraction):
        analitico = _qber_medido(MOTOR_ANALITICO, noise_rate, eve_fraction, seed=2)
        cuantico = _qber_medido(MOTOR_QISKIT, noise_rate, eve_fraction, seed=2)

        assert abs(analitico - cuantico) < TOLERANCIA, (
            f'ruido={noise_rate} eve={eve_fraction}: '
            f'analítico {analitico:.4f} vs qiskit {cuantico:.4f}'
        )

    def test_sin_perturbacion_ambos_motores_son_exactos(self):
        """Sin ruido ni espía, Bob reproduce los bits cribados en los dos motores."""
        for motor in (MOTOR_ANALITICO, MOTOR_QISKIT):
            r = simulate_bb84(500, has_eve=False, engine=motor, seed=8)
            for i in r.sifted_indices:
                assert r.bob_results[i] == r.alice_bits[i], f'falló en {motor}'


class TestSeleccionDeMotor:
    """El motor se elige explícitamente y degrada solo si falta Qiskit."""

    def test_el_motor_analitico_no_necesita_qiskit(self):
        r = simulate_bb84(64, engine=MOTOR_ANALITICO, seed=1)
        assert r.engine == MOTOR_ANALITICO

    @requiere_qiskit
    def test_pedir_qiskit_usa_qiskit(self):
        r = simulate_bb84(64, engine=MOTOR_QISKIT, seed=1)
        assert r.engine == MOTOR_QISKIT


class TestReproducibilidad:
    """Una misma semilla tiene que reproducir la corrida completa."""

    @pytest.mark.parametrize('motor', [MOTOR_ANALITICO,
                                       pytest.param(MOTOR_QISKIT, marks=requiere_qiskit)])
    def test_la_semilla_reproduce_la_corrida(self, motor):
        """Aer tiene su propio RNG: sin sembrarlo, el motor de Qiskit daba
        resultados distintos aunque se fijara la semilla del protocolo."""
        corridas = [
            simulate_bb84(800, has_eve=True, engine=motor, seed=99)
            for _ in range(3)
        ]
        primera = corridas[0]
        for otra in corridas[1:]:
            assert otra.alice_bits == primera.alice_bits
            assert otra.bob_results == primera.bob_results
            assert otra.eve_bits == primera.eve_bits
            assert otra.error_rate == primera.error_rate

    @pytest.mark.parametrize('motor', [MOTOR_ANALITICO,
                                       pytest.param(MOTOR_QISKIT, marks=requiere_qiskit)])
    def test_semillas_distintas_dan_corridas_distintas(self, motor):
        a = simulate_bb84(800, has_eve=True, engine=motor, seed=1)
        b = simulate_bb84(800, has_eve=True, engine=motor, seed=2)
        assert a.bob_results != b.bob_results
