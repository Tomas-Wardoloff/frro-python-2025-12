"""
Estructura de resultado del protocolo BB84.

Antes ``simulate_bb84`` devolvía un diccionario suelto que no incluía los bits ni
las bases, así que la capa de presentación no tenía con qué dibujar el protocolo
y terminaba inventando datos con ``Math.random()`` en el browser. Este dataclass
transporta la traza completa de la corrida.
"""
from dataclasses import dataclass, field
from typing import List, Optional

# Cuántos bits de la traza se persisten. Una corrida de 1000 bits guardaría
# ~6 listas de 1000 enteros; recortar acota el tamaño de la fila sin perder
# valor didáctico (la animación muestra muchos menos).
MAX_TRACE_BITS = 256


@dataclass
class BB84Result:
    """Resultado completo de una corrida del protocolo BB84."""

    # Parámetros de entrada
    key_length: int
    noise_rate: float
    eve_strategy: str
    eve_fraction: float
    engine: str

    # Traza del protocolo (una entrada por qubit transmitido)
    alice_bits: List[int] = field(default_factory=list)
    alice_bases: List[int] = field(default_factory=list)
    bob_bases: List[int] = field(default_factory=list)
    bob_results: List[int] = field(default_factory=list)
    # -1 donde Eve no intervino
    eve_bases: List[int] = field(default_factory=list)
    eve_bits: List[int] = field(default_factory=list)
    intercepted: List[bool] = field(default_factory=list)

    # Cribado y verificación
    sifted_indices: List[int] = field(default_factory=list)
    sample_indices: List[int] = field(default_factory=list)

    # Salida
    success: bool = True
    result: str = 'secure'          # 'secure' | 'compromised'
    final_key: Optional[str] = None
    eve_key: Optional[str] = None   # lo que Eve cree que es la clave
    error_rate: float = 0.0
    message: str = ''

    @property
    def sifted_length(self) -> int:
        return len(self.sifted_indices)

    @property
    def final_length(self) -> int:
        return len(self.final_key) if self.final_key else 0

    @property
    def matching_bases(self) -> int:
        return len(self.sifted_indices)

    def summary(self) -> dict:
        """Métricas de la corrida, sin la traza (para guardar y para el historial)."""
        return {
            'success': self.success,
            'result': self.result,
            'final_key': self.final_key,
            'error_rate': self.error_rate,
            'message': self.message,
            'key_length_initial': self.key_length,
            'key_length_after_sifting': self.sifted_length,
            'key_length_final': self.final_length,
            'matching_bases': self.matching_bases,
            'noise_rate': self.noise_rate,
            'eve_strategy': self.eve_strategy,
            'eve_fraction': self.eve_fraction,
            'engine': self.engine,
        }

    def trace(self, limit: int = MAX_TRACE_BITS) -> dict:
        """Traza bit a bit, recortada a ``limit`` qubits.

        Los índices de cribado y de muestra se filtran al mismo recorte para que
        sigan siendo coherentes con las listas que se devuelven.
        """
        n = min(limit, self.key_length)
        sample = set(self.sample_indices)
        return {
            'alice_bits': self.alice_bits[:n],
            'alice_bases': self.alice_bases[:n],
            'bob_bases': self.bob_bases[:n],
            'bob_results': self.bob_results[:n],
            'eve_bases': self.eve_bases[:n],
            'eve_bits': self.eve_bits[:n],
            'intercepted': self.intercepted[:n],
            'sifted_indices': [i for i in self.sifted_indices if i < n],
            # sample_indices indexa la clave cribada, no la transmisión
            'sample_positions': sorted(
                pos for pos, idx in enumerate(self.sifted_indices)
                if pos in sample and idx < n
            ),
            'shown_bits': n,
            'total_bits': self.key_length,
        }

    def is_truncated(self, limit: int = MAX_TRACE_BITS) -> bool:
        return self.key_length > limit
