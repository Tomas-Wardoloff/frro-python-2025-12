"""
Protocolo BB84: cribado de bases, estimación de QBER y decisión de seguridad.

La lógica del protocolo vive acá y es independiente del motor que resuelva el
canal: ``engines.analytic`` (forma cerrada) o ``engines.qiskit_engine``
(circuitos cuánticos). Ambos exponen la misma función ``transmitir``.
"""
import random

from business.bb84.engines import analytic, qiskit_engine
from business.bb84.result import BB84Result

# Umbral clásico de QBER para BB84. Por encima de este valor la clave se
# descarta: la información que podría haber filtrado un espía ya no se puede
# compensar con amplificación de privacidad.
UMBRAL_QBER = 0.11

# Estrategias de Eve
EVE_NINGUNA = 'none'
EVE_INTERCEPT_RESEND = 'intercept_resend'
ESTRATEGIAS = (EVE_NINGUNA, EVE_INTERCEPT_RESEND)

# Motores disponibles
MOTOR_ANALITICO = 'analytic'
MOTOR_QISKIT = 'qiskit'

# Mínimo de bits cribados para poder estimar el QBER y que sobre clave.
# Por debajo de esto la corrida no sirve: no hay muestra estadística.
MIN_BITS_CRIBADOS = 4

# Tope de bits que se gastan en la verificación pública
MAX_BITS_MUESTRA = 20


def _elegir_motor(engine):
    """Devuelve el módulo motor, cayendo al analítico si Qiskit no está."""
    if engine == MOTOR_QISKIT:
        if not qiskit_engine.disponible():
            return analytic, MOTOR_ANALITICO
        return qiskit_engine, MOTOR_QISKIT
    return analytic, MOTOR_ANALITICO


def motores_disponibles():
    """Lista de motores utilizables en este entorno."""
    motores = [MOTOR_ANALITICO]
    if qiskit_engine.disponible():
        motores.append(MOTOR_QISKIT)
    return motores


def simulate_bb84(key_length, has_eve=False, *, noise_rate=0.0,
                  eve_strategy=None, eve_fraction=1.0,
                  engine=MOTOR_ANALITICO, seed=None):
    """Ejecuta el protocolo BB84 completo.

    Args:
        key_length: cantidad de qubits que transmite Alice.
        has_eve: atajo retrocompatible. ``True`` equivale a
            ``eve_strategy='intercept_resend'`` con ``eve_fraction=1.0``.
        noise_rate: probabilidad de bit-flip en el detector de Bob (0.0 a 1.0).
        eve_strategy: ``'none'`` o ``'intercept_resend'``. Si se omite, se
            deduce de ``has_eve``.
        eve_fraction: fracción de qubits que Eve intercepta (0.0 a 1.0).
        engine: ``'analytic'`` o ``'qiskit'``.
        seed: semilla para corridas reproducibles.

    Returns:
        BB84Result: resultado con la traza completa del protocolo.
    """
    rng = random.Random(seed)

    # Normalizar la configuración de Eve
    if eve_strategy is None:
        eve_strategy = EVE_INTERCEPT_RESEND if has_eve else EVE_NINGUNA
    if eve_strategy not in ESTRATEGIAS:
        raise ValueError(f'Estrategia de Eve desconocida: {eve_strategy!r}')
    if eve_strategy == EVE_NINGUNA:
        eve_fraction = 0.0
    eve_fraction = min(max(eve_fraction, 0.0), 1.0)
    noise_rate = min(max(noise_rate, 0.0), 1.0)

    motor, nombre_motor = _elegir_motor(engine)

    resultado = BB84Result(
        key_length=key_length,
        noise_rate=noise_rate,
        eve_strategy=eve_strategy,
        eve_fraction=eve_fraction,
        engine=nombre_motor,
    )

    # Paso 1 y 2: Alice y Bob eligen bits y bases al azar
    resultado.alice_bits = [rng.randint(0, 1) for _ in range(key_length)]
    resultado.alice_bases = [rng.randint(0, 1) for _ in range(key_length)]
    resultado.bob_bases = [rng.randint(0, 1) for _ in range(key_length)]

    # Paso 3: transmisión por el canal cuántico
    bob_results, eve_bases, eve_bits, intercepted = motor.transmitir(
        resultado.alice_bits,
        resultado.alice_bases,
        resultado.bob_bases,
        eve_fraction=eve_fraction,
        noise_rate=noise_rate,
        rng=rng,
    )
    resultado.bob_results = bob_results
    resultado.eve_bases = eve_bases
    resultado.eve_bits = eve_bits
    resultado.intercepted = intercepted

    # Paso 4: comparación pública de bases (cribado)
    resultado.sifted_indices = [
        i for i in range(key_length)
        if resultado.alice_bases[i] == resultado.bob_bases[i]
    ]
    alice_key = [resultado.alice_bits[i] for i in resultado.sifted_indices]
    bob_key = [resultado.bob_results[i] for i in resultado.sifted_indices]

    # Con muy pocos bits cribados no hay forma de estimar el QBER.
    # (Antes esto derivaba en una división por cero cuando la clave cribada
    # tenía menos de 4 bits, algo que pasaba ~20% de las veces con
    # key_length=10, que es el mínimo que acepta el formulario.)
    if len(alice_key) < MIN_BITS_CRIBADOS:
        resultado.success = False
        resultado.result = 'aborted'
        resultado.message = (
            f'Coincidieron sólo {len(alice_key)} bases de {key_length} qubits: '
            f'hacen falta al menos {MIN_BITS_CRIBADOS} bits cribados para '
            'estimar el error. Probá con una longitud de clave mayor.'
        )
        return resultado

    # Paso 5: verificación pública de una muestra
    tamano_muestra = max(1, min(len(alice_key) // 4, MAX_BITS_MUESTRA))
    indices_muestra = rng.sample(range(len(alice_key)), tamano_muestra)
    resultado.sample_indices = sorted(indices_muestra)

    errores = sum(1 for i in indices_muestra if alice_key[i] != bob_key[i])
    resultado.error_rate = errores / tamano_muestra

    # Paso 6: los bits revelados se descartan; el resto es la clave
    en_muestra = set(indices_muestra)
    bits_finales = [
        alice_key[i] for i in range(len(alice_key)) if i not in en_muestra
    ]
    bits_eve = [
        resultado.eve_bits[resultado.sifted_indices[i]]
        for i in range(len(alice_key)) if i not in en_muestra
    ]

    # Paso 7: regla de negocio — decidir si la clave es utilizable
    if resultado.error_rate < UMBRAL_QBER:
        resultado.result = 'secure'
        resultado.final_key = ''.join(map(str, bits_finales))
        # Lo que Eve cree tener: '?' donde no interceptó
        resultado.eve_key = ''.join(
            '?' if b < 0 else str(b) for b in bits_eve
        )
        resultado.message = (
            f'Clave segura de {len(bits_finales)} bits. QBER: '
            f'{resultado.error_rate:.2%}'
        )
    else:
        resultado.result = 'compromised'
        resultado.final_key = None
        resultado.eve_key = None
        resultado.message = (
            f'Clave descartada: QBER {resultado.error_rate:.2%} supera el '
            f'umbral de {UMBRAL_QBER:.0%}. {_diagnostico(resultado)}'
        )

    return resultado


def _diagnostico(resultado):
    """Explica a qué se atribuye un QBER alto.

    Regla de negocio: el protocolo aborta ante un QBER alto **sin poder
    distinguir** si lo causó un espía o un canal ruidoso. Esa indistinguibilidad
    es justamente la garantía de BB84, y también su límite práctico: un enlace
    demasiado ruidoso es inutilizable aunque no haya nadie escuchando.
    """
    if resultado.noise_rate >= UMBRAL_QBER:
        return (
            f'El ruido del canal ({resultado.noise_rate:.0%}) alcanza por sí '
            'solo para superar el umbral: el enlace es inutilizable aunque no '
            'haya espía.'
        )
    if resultado.eve_fraction > 0:
        return 'Compatible con un ataque de interceptación y reenvío.'
    return (
        'No hubo espía en esta corrida: el error viene del ruido del canal. '
        'El protocolo descarta la clave igual, porque no puede distinguir '
        'una causa de la otra.'
    )


def qber_esperado(noise_rate, eve_fraction):
    """QBER teórico para los parámetros dados.

    Sobre los bits cribados, un ataque de interceptación y reenvío introduce
    error en 1/4 de los qubits que toca (Eve erra la base la mitad de las veces
    y, cuando eso pasa, Bob recibe un bit al azar que es incorrecto la mitad de
    las veces). El ruido del detector aporta su propia probabilidad de flip.

    Se usa en los tests para validar los motores contra la teoría.
    """
    p_eve = 0.25 * eve_fraction
    # Dos fuentes independientes de error: se combinan como XOR de probabilidades
    return p_eve + noise_rate - 2 * p_eve * noise_rate
