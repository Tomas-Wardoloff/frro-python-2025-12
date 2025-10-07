"""
Simulación del Protocolo BB84 usando Qiskit
Este archivo contiene la implementación completa del protocolo cuántico
"""
import random
import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram


def generate_random_bits(n):
    """Genera n bits aleatorios"""
    return [random.randint(0, 1) for _ in range(n)]


def generate_random_bases(n):
    """Genera n bases aleatorias (0=rectilínea +, 1=diagonal x)"""
    return [random.randint(0, 1) for _ in range(n)]


def encode_qubit(bit, basis):
    """
    Codifica un bit en un qubit según la base
    
    Args:
        bit (int): 0 o 1
        basis (int): 0 (base +) o 1 (base x)
    
    Returns:
        QuantumCircuit: Circuito con el qubit codificado
    """
    qc = QuantumCircuit(1, 1)
    
    # Codificar el bit
    if bit == 1:
        qc.x(0)  # Aplicar NOT si el bit es 1
    
    # Aplicar Hadamard si la base es diagonal (x)
    if basis == 1:
        qc.h(0)
    
    return qc


def measure_qubit(qc, basis):
    """
    Mide un qubit en la base especificada
    
    Args:
        qc (QuantumCircuit): Circuito cuántico
        basis (int): Base de medición (0=+, 1=x)
    
    Returns:
        QuantumCircuit: Circuito con la medición aplicada
    """
    # Si la base es diagonal, aplicar Hadamard antes de medir
    if basis == 1:
        qc.h(0)
    
    qc.measure(0, 0)
    return qc


def eve_intercept(qc):
    """
    Simula la interceptación y medición de Eve
    Eve mide con una base aleatoria e intenta reenviar
    
    Args:
        qc (QuantumCircuit): Circuito a interceptar
    
    Returns:
        tuple: (circuito modificado, base usada por Eve, resultado de Eve)
    """
    eve_basis = random.randint(0, 1)
    
    # Eve mide con su base aleatoria
    if eve_basis == 1:
        qc.h(0)
    qc.measure(0, 0)
    
    # Simular ejecución para obtener el resultado de Eve
    simulator = Aer.get_backend('qasm_simulator')
    job = simulator.run(qc, shots=1)
    result = job.result()
    counts = result.get_counts()
    eve_bit = int(list(counts.keys())[0])
    
    # Eve prepara un nuevo qubit con lo que midió
    qc_new = QuantumCircuit(1, 1)
    if eve_bit == 1:
        qc_new.x(0)
    if eve_basis == 1:
        qc_new.h(0)
    
    return qc_new, eve_basis, eve_bit


def simulate_bb84(key_length, has_eve=False):
    """
    Simula el protocolo BB84 completo
    
    Args:
        key_length (int): Longitud de la secuencia inicial
        has_eve (bool): Si hay espía o no
    
    Returns:
        dict: Resultado de la simulación
    """
    # Paso 1: Alice genera bits y bases aleatorias
    alice_bits = generate_random_bits(key_length)
    alice_bases = generate_random_bases(key_length)
    
    # Paso 2: Bob genera bases aleatorias
    bob_bases = generate_random_bases(key_length)
    
    # Paso 3: Transmisión y medición de qubits
    bob_results = []
    simulator = Aer.get_backend('qasm_simulator')
    
    for i in range(key_length):
        # Alice codifica su bit
        qc = encode_qubit(alice_bits[i], alice_bases[i])
        
        # Si hay Eve, intercepta
        if has_eve:
            qc, eve_basis, eve_bit = eve_intercept(qc)
        
        # Bob mide con su base
        qc = measure_qubit(qc, bob_bases[i])
        
        # Ejecutar el circuito
        job = simulator.run(qc, shots=1)
        result = job.result()
        counts = result.get_counts()
        bob_bit = int(list(counts.keys())[0])
        bob_results.append(bob_bit)
    
    # Paso 4: Comparación pública de bases
    matching_bases_indices = [i for i in range(key_length) if alice_bases[i] == bob_bases[i]]
    
    # Paso 5: Clave filtrada (donde las bases coinciden)
    alice_key = [alice_bits[i] for i in matching_bases_indices]
    bob_key = [bob_results[i] for i in matching_bases_indices]
    
    # Paso 6: Calcular tasa de error (QBER)
    if len(alice_key) == 0:
        return {
            'success': False,
            'message': 'No hubo coincidencia de bases suficiente'
        }
    
    # Comparar una muestra para detectar espionaje
    sample_size = min(len(alice_key) // 4, 20)  # 25% de la clave o máximo 20 bits
    sample_indices = random.sample(range(len(alice_key)), sample_size)
    
    errors = sum(1 for i in sample_indices if alice_key[i] != bob_key[i])
    error_rate = errors / sample_size
    
    # Paso 7: Decidir si la clave es segura
    THRESHOLD = 0.11  # Umbral típico para BB84
    
    if error_rate < THRESHOLD:
        # Remover los bits usados en la verificación
        final_key_bits = [alice_key[i] for i in range(len(alice_key)) if i not in sample_indices]
        final_key = ''.join(map(str, final_key_bits))
        
        return {
            'success': True,
            'result': 'secure',
            'final_key': final_key,
            'error_rate': error_rate,
            'key_length_initial': key_length,
            'key_length_after_sifting': len(alice_key),
            'key_length_final': len(final_key_bits),
            'matching_bases': len(matching_bases_indices),
            'message': f'Clave segura generada. QBER: {error_rate:.2%}'
        }
    else:
        return {
            'success': True,
            'result': 'compromised',
            'final_key': None,
            'error_rate': error_rate,
            'key_length_initial': key_length,
            'key_length_after_sifting': len(alice_key),
            'key_length_final': 0,
            'matching_bases': len(matching_bases_indices),
            'message': f'¡Espionaje detectado! QBER demasiado alto: {error_rate:.2%}'
        }


# TODO: Integrar esta función en simulation_controller.py
