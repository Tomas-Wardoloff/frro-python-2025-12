"""
Motor del canal BB84 sobre circuitos cuánticos reales (Qiskit + Aer).

Simula cada transmisión como un circuito de un qubit: Alice prepara el estado
con X y H, Eve (si intercepta) mide y reenvía, y Bob mide en su base.

Diferencias con la implementación original:

- Los circuitos se ejecutan **en lote** (una sola llamada a ``simulator.run``
  con la lista completa) en vez de una llamada por bit, y el backend se obtiene
  una sola vez en lugar de una vez por qubit interceptado.
- El ruido del detector se aplica igual que en el motor analítico (bit-flip
  clásico sobre el resultado), para que ambos motores modelen exactamente el
  mismo canal y la comparación entre ellos sea significativa.

Qiskit es una dependencia **opcional**: si no está instalado, ``disponible()``
devuelve False y ``business.bb84.protocol`` cae al motor analítico.
"""
import random

try:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator
    QISKIT_DISPONIBLE = True
except ImportError:  # pragma: no cover - depende del entorno
    QuantumCircuit = None
    AerSimulator = None
    QISKIT_DISPONIBLE = False

SIN_EVE = -1

BASE_RECTILINEA = 0
BASE_DIAGONAL = 1


def disponible():
    """Indica si Qiskit y Aer se pudieron importar."""
    return QISKIT_DISPONIBLE


def _preparar(bit, base):
    """Circuito de 1 qubit con ``bit`` codificado en ``base``."""
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)
    if base == BASE_DIAGONAL:
        qc.h(0)
    return qc


def _medir(qc, base):
    """Agrega al circuito la medición en la base indicada."""
    if base == BASE_DIAGONAL:
        qc.h(0)
    qc.measure(0, 0)
    return qc


def _correr_lote(simulator, circuitos):
    """Ejecuta todos los circuitos en una sola llamada y devuelve los bits."""
    if not circuitos:
        return []
    resultado = simulator.run(circuitos, shots=1).result()
    bits = []
    for idx in range(len(circuitos)):
        counts = resultado.get_counts(idx)
        bits.append(int(next(iter(counts))))
    return bits


def transmitir(alice_bits, alice_bases, bob_bases, *,
               eve_fraction=0.0, noise_rate=0.0, rng=None):
    """Misma interfaz que ``analytic.transmitir``, resuelta con circuitos.

    Returns:
        tuple: (bob_results, eve_bases, eve_bits, intercepted)
    """
    if not QISKIT_DISPONIBLE:
        raise RuntimeError(
            'Qiskit no está instalado. Instalá qiskit y qiskit-aer, o usá '
            "engine='analytic'."
        )

    rng = rng or random
    simulator = AerSimulator()
    n = len(alice_bits)

    # --- Etapa 1: Eve mide los qubits que decide interceptar ---
    eve_bases = [SIN_EVE] * n
    eve_bits = [SIN_EVE] * n
    intercepted = [False] * n

    indices_eve = []
    circuitos_eve = []
    for i in range(n):
        if eve_fraction > 0 and rng.random() < eve_fraction:
            base_eve = rng.randint(0, 1)
            eve_bases[i] = base_eve
            intercepted[i] = True
            indices_eve.append(i)
            circuitos_eve.append(_medir(_preparar(alice_bits[i], alice_bases[i]), base_eve))

    for i, bit in zip(indices_eve, _correr_lote(simulator, circuitos_eve)):
        eve_bits[i] = bit

    # --- Etapa 2: Bob mide lo que llega (reenviado por Eve o original) ---
    circuitos_bob = []
    for i in range(n):
        if intercepted[i]:
            # Eve reenvía lo que midió, en su propia base
            qc = _preparar(eve_bits[i], eve_bases[i])
        else:
            qc = _preparar(alice_bits[i], alice_bases[i])
        circuitos_bob.append(_medir(qc, bob_bases[i]))

    bob_results = _correr_lote(simulator, circuitos_bob)

    # --- Etapa 3: ruido del detector (idéntico al motor analítico) ---
    if noise_rate > 0:
        bob_results = [
            bit ^ 1 if rng.random() < noise_rate else bit
            for bit in bob_results
        ]

    return bob_results, eve_bases, eve_bits, intercepted
