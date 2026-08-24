"""
Capa de Negocio - Simulación del protocolo BB84.

El paquete separa la lógica del protocolo (``protocol``) de la resolución física
del canal (``engines``), de modo que la misma simulación pueda correr sobre un
modelo analítico o sobre circuitos cuánticos de Qiskit.
"""
from business.bb84.protocol import (
    ESTRATEGIAS,
    EVE_INTERCEPT_RESEND,
    EVE_NINGUNA,
    MOTOR_ANALITICO,
    MOTOR_QISKIT,
    UMBRAL_QBER,
    motores_disponibles,
    qber_esperado,
    simulate_bb84,
)
from business.bb84.result import BB84Result, MAX_TRACE_BITS

__all__ = [
    'BB84Result',
    'ESTRATEGIAS',
    'EVE_INTERCEPT_RESEND',
    'EVE_NINGUNA',
    'MAX_TRACE_BITS',
    'MOTOR_ANALITICO',
    'MOTOR_QISKIT',
    'UMBRAL_QBER',
    'motores_disponibles',
    'qber_esperado',
    'simulate_bb84',
]
