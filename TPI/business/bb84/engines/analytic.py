"""
Motor analítico del canal BB84.

BB84 es un protocolo *prepare-and-measure* de un solo qubit por transmisión: el
resultado de cada medición tiene forma cerrada y no hace falta simular el
circuito para obtenerlo. Este motor calcula esos resultados directamente.

Sirve para dos cosas:

1. Es el motor por defecto: no depende de Qiskit, que con SciPy pesa ~130 MB y
   no entra en los límites de tamaño de varias plataformas de deploy.
2. Es el modelo teórico contra el que se contrasta el motor de Qiskit
   (ver ``tests/test_engines.py``): si ambos coinciden estadísticamente, el
   modelo analítico queda validado contra un simulador cuántico real.

Reglas del canal
----------------
- Si Bob mide en la misma base en la que se preparó el qubit, obtiene el bit
  preparado con certeza.
- Si mide en la base conjugada, el resultado es aleatorio (50/50).
- Eve (intercept-resend) mide en una base al azar y **reenvía** lo que midió en
  esa base, con lo que altera el estado cuando erró la base.
- El ruido se modela como bit-flip clásico del detector de Bob con probabilidad
  ``noise_rate``, independiente de la base. Es lo que aportan el desalineamiento
  y las cuentas oscuras en un enlace real.
"""
import random

BASE_RECTILINEA = 0
BASE_DIAGONAL = 1

SIN_EVE = -1


def transmitir(alice_bits, alice_bases, bob_bases, *,
               eve_fraction=0.0, noise_rate=0.0, rng=None):
    """Propaga cada qubit por el canal y devuelve lo que mide Bob.

    Args:
        alice_bits: bits que prepara Alice.
        alice_bases: bases en las que los prepara.
        bob_bases: bases en las que mide Bob.
        eve_fraction: fracción de qubits que Eve intercepta (0.0 a 1.0).
        noise_rate: probabilidad de bit-flip en el detector de Bob.
        rng: instancia de ``random.Random`` para corridas reproducibles.

    Returns:
        tuple: (bob_results, eve_bases, eve_bits, intercepted)
    """
    rng = rng or random

    n = len(alice_bits)
    bob_results = []
    eve_bases = []
    eve_bits = []
    intercepted = []

    for i in range(n):
        # Estado que viaja por el canal: (bit, base) en que fue preparado
        bit_actual = alice_bits[i]
        base_actual = alice_bases[i]

        # --- Eve ---
        if eve_fraction > 0 and rng.random() < eve_fraction:
            base_eve = rng.randint(0, 1)
            if base_eve == base_actual:
                # Base correcta: Eve lee el bit sin perturbar el estado
                bit_eve = bit_actual
            else:
                # Base equivocada: resultado al azar y el estado colapsa
                bit_eve = rng.randint(0, 1)

            eve_bases.append(base_eve)
            eve_bits.append(bit_eve)
            intercepted.append(True)

            # Eve reenvía lo que midió, en su propia base
            bit_actual = bit_eve
            base_actual = base_eve
        else:
            eve_bases.append(SIN_EVE)
            eve_bits.append(SIN_EVE)
            intercepted.append(False)

        # --- Bob ---
        if bob_bases[i] == base_actual:
            bit_bob = bit_actual
        else:
            bit_bob = rng.randint(0, 1)

        # --- Ruido del detector ---
        if noise_rate > 0 and rng.random() < noise_rate:
            bit_bob ^= 1

        bob_results.append(bit_bob)

    return bob_results, eve_bases, eve_bits, intercepted
