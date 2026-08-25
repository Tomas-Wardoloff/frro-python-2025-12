"""
Capa de Negocio - Cifrado one-time-pad con la clave generada por BB84.

Es el paso que le da sentido a todo lo anterior: la clave que Alice y Bob
acordaron por el canal cuántico se usa para cifrar un mensaje real.

El one-time-pad es el único cifrado con seguridad demostrada de forma
incondicional, pero exige tres condiciones que BB84 justamente provee o impone:
la clave debe ser verdaderamente aleatoria, tan larga como el mensaje, y usarse
una sola vez.
"""

# Un carácter ocupa 8 bits de clave
BITS_POR_CARACTER = 8

MAX_MENSAJE = 512


def bits_necesarios(mensaje):
    """Cuántos bits de clave hacen falta para cifrar ``mensaje``."""
    return len(mensaje.encode('utf-8')) * BITS_POR_CARACTER


def _clave_a_bits(clave):
    """Convierte la clave de texto ('0101...') a lista de enteros."""
    return [1 if c == '1' else 0 for c in clave]


def _xor(datos, bits_clave):
    """Aplica XOR byte a byte entre los datos y la clave."""
    salida = bytearray()
    for i, byte in enumerate(datos):
        mascara = 0
        for j in range(BITS_POR_CARACTER):
            mascara = (mascara << 1) | bits_clave[i * BITS_POR_CARACTER + j]
        salida.append(byte ^ mascara)
    return bytes(salida)


def validar(mensaje, clave, resultado_sesion):
    """
    Valida las precondiciones del cifrado.

    Reglas de negocio:
      1. No se cifra con una clave de una sesión comprometida: si el QBER
         superó el umbral, Eve puede tener información sobre esos bits.
      2. La clave tiene que ser al menos tan larga como el mensaje. Reutilizar
         o estirar la clave rompe la garantía del one-time-pad.

    Returns:
        str | None: mensaje de error, o None si se puede cifrar
    """
    if not mensaje:
        return 'Escribí un mensaje para cifrar'

    if len(mensaje) > MAX_MENSAJE:
        return f'El mensaje no puede superar los {MAX_MENSAJE} caracteres'

    if resultado_sesion != 'secure':
        return (
            'Esta clave provino de una sesión comprometida. Usarla rompería la '
            'garantía del protocolo: si el QBER superó el umbral, Eve puede '
            'conocer parte de esos bits.'
        )

    if not clave:
        return 'La sesión no generó ninguna clave'

    faltan = bits_necesarios(mensaje) - len(clave)
    if faltan > 0:
        return (
            f'La clave es demasiado corta: hacen falta {bits_necesarios(mensaje)} '
            f'bits para este mensaje y la sesión generó {len(clave)}. '
            f'Acortá el mensaje o corré una simulación con más qubits.'
        )

    return None


def cifrar(mensaje, clave, resultado_sesion, clave_de_eve=None):
    """
    Cifra un mensaje con one-time-pad usando la clave de la sesión.

    Args:
        mensaje (str): Texto a cifrar
        clave (str): Clave final de la sesión, como cadena de bits
        resultado_sesion (str): 'secure' o 'compromised'
        clave_de_eve (str, optional): Lo que Eve cree que es la clave, con '?'
            en las posiciones que no pudo medir

    Returns:
        dict: Resultado con el texto cifrado y, si corresponde, el intento
              fallido de descifrado de Eve
    """
    error = validar(mensaje, clave, resultado_sesion)
    if error:
        return {'success': False, 'message': error}

    datos = mensaje.encode('utf-8')
    bits = _clave_a_bits(clave)
    cifrado = _xor(datos, bits)

    salida = {
        'success': True,
        'message': 'Mensaje cifrado con la clave de esta sesión',
        'texto_plano': mensaje,
        'cifrado_hex': cifrado.hex(),
        'bits_usados': bits_necesarios(mensaje),
        'bits_disponibles': len(clave),
        # Se descifra con la misma clave: demuestra que Bob recupera el original
        'descifrado_por_bob': _xor(cifrado, bits).decode('utf-8', errors='replace'),
    }

    # Qué obtendría Eve con su conocimiento parcial de la clave
    if clave_de_eve:
        necesarios = bits_necesarios(mensaje)
        parcial = clave_de_eve[:necesarios]
        if len(parcial) == necesarios:
            # Donde Eve no midió pone un bit al azar; se usa 0 para ilustrar
            bits_eve = [0 if c not in ('0', '1') else int(c) for c in parcial]
            intento = _xor(cifrado, bits_eve)
            salida['descifrado_por_eve'] = intento.decode('utf-8', errors='replace')
            salida['bits_que_eve_desconoce'] = parcial.count('?')

    return salida
