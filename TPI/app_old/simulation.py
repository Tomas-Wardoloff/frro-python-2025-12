# app/simulation.py

import random


def generate_alice_sequence(key_length: int):
    """
    Genera la secuencia inicial de Alice.

    Args:
        key_length (int): La longitud deseada para la clave inicial.

    Returns:
        tuple: Una tupla conteniendo dos listas:
               - La primera lista con los bits aleatorios de Alice (0s y 1s).
               - La segunda lista con las bases aleatorias de Alice (0 para base + y 1 para base x).
    """
    alice_bits = []
    alice_bases = []

    for _ in range(key_length):
        # Generamos un bit aleatorio (0 o 1)
        bit = random.randint(0, 1)
        alice_bits.append(bit)

        # Generamos una base aleatoria (0 o 1)
        # Convención: 0 = base rectilínea (+), 1 = base diagonal (x)
        base = random.randint(0, 1)
        alice_bases.append(base)

    return alice_bits, alice_bases


# Este bloque solo se ejecuta si corremos el archivo directamente
# (ej: python app/simulation.py) y no cuando se importa.
if __name__ == '__main__':
    N = 10  # Probemos con una clave de 10 bits
    bits, bases = generate_alice_sequence(N)

    print(f"Probando la generación de secuencias para N={N}")
    print(f"Bits de Alice:  {bits}")
    print(f"Bases de Alice: {bases}")
    print(f"Longitud de bits:  {len(bits)}")
    print(f"Longitud de bases: {len(bases)}")
