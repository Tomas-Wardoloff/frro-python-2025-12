"""
Capa de Negocio - Controlador de Simulación
Contiene la lógica de negocio del protocolo BB84
NO accede directamente a la base de datos, usa la capa de datos
"""
from business.bb84 import MOTOR_ANALITICO, simulate_bb84
from datos import session_repository

# Reglas de negocio sobre los parámetros de la simulación
MIN_KEY_LENGTH = 10
MAX_KEY_LENGTH = 1000
MAX_NOISE_RATE = 0.5


def get_user_simulation_history(user_id, limit=10, offset=None):
    """
    Obtiene el historial de simulaciones de un usuario

    Args:
        user_id (int): ID del usuario
        limit (int): Número máximo de resultados
        offset (int, optional): Desplazamiento para paginar

    Returns:
        list: Lista de sesiones en formato diccionario
    """
    sessions = session_repository.get_user_sessions(user_id, limit, offset)
    return [session.to_dict() for session in sessions]


def get_user_statistics(user_id):
    """
    Obtiene estadísticas de las simulaciones de un usuario
    Regla de negocio: Calcula métricas agregadas

    El conteo se resuelve en SQL en vez de traer todas las filas a memoria.

    Args:
        user_id (int): ID del usuario

    Returns:
        dict: Estadísticas del usuario
    """
    por_resultado = session_repository.count_sessions_by_result(user_id)

    secure = por_resultado.get('secure', 0)
    compromised = por_resultado.get('compromised', 0)
    total = sum(por_resultado.values())

    return {
        'total_simulations': total,
        'secure_simulations': secure,
        'compromised_simulations': compromised,
        'success_rate': round((secure / total) * 100, 2) if total > 0 else 0.0
    }


def validar_parametros(key_length, noise_rate=0.0, eve_fraction=1.0):
    """
    Valida los parámetros de una simulación.

    Regla de negocio: la longitud de clave tiene que estar en un rango donde el
    protocolo sea estadísticamente significativo y el cómputo acotado.

    Returns:
        str | None: mensaje de error, o None si los parámetros son válidos
    """
    if key_length is None:
        return 'Debe indicar la longitud de la clave'

    if key_length < MIN_KEY_LENGTH:
        return f'La longitud de la clave debe ser al menos {MIN_KEY_LENGTH} bits'

    if key_length > MAX_KEY_LENGTH:
        return f'La longitud de la clave no puede exceder {MAX_KEY_LENGTH} bits'

    if not 0.0 <= noise_rate <= MAX_NOISE_RATE:
        return f'El ruido del canal debe estar entre 0% y {MAX_NOISE_RATE:.0%}'

    if not 0.0 <= eve_fraction <= 1.0:
        return 'La fracción interceptada por Eve debe estar entre 0% y 100%'

    return None


def run_bb84_simulation(user_id, key_length, has_eve, *, noise_rate=0.0,
                        eve_strategy=None, eve_fraction=1.0,
                        engine=MOTOR_ANALITICO):
    """
    Ejecuta la simulación completa del protocolo BB84 y la registra

    Args:
        user_id (int): ID del usuario que ejecuta la simulación
        key_length (int): Longitud de la clave inicial
        has_eve (bool): Si incluir un espía o no
        noise_rate (float): Ruido del canal (0.0 a 0.5)
        eve_strategy (str, optional): 'none' o 'intercept_resend'
        eve_fraction (float): Fracción de qubits que Eve intercepta
        engine (str): 'analytic' o 'qiskit'

    Returns:
        dict: Resultado de la simulación, con la traza del protocolo
    """
    error = validar_parametros(key_length, noise_rate, eve_fraction)
    if error:
        return {'success': False, 'message': error}

    try:
        resultado = simulate_bb84(
            key_length,
            has_eve,
            noise_rate=noise_rate,
            eve_strategy=eve_strategy,
            eve_fraction=eve_fraction,
            engine=engine,
        )
    except Exception as exc:  # noqa: BLE001 - la vista necesita un mensaje
        return {'success': False, 'message': f'Error en la simulación: {exc}'}

    # Una corrida abortada (muy pocas bases coincidentes) no se guarda:
    # no produjo ni clave ni una estimación de error utilizable.
    if not resultado.success:
        return {'success': False, 'message': resultado.message}

    traza = resultado.trace()

    session = session_repository.create_session(
        user_id=user_id,
        key_length=key_length,
        has_eve=resultado.eve_fraction > 0,
        result=resultado.result,
        final_key=resultado.final_key,
        error_rate=resultado.error_rate,
        noise_rate=resultado.noise_rate,
        eve_strategy=resultado.eve_strategy,
        eve_fraction=resultado.eve_fraction,
        engine=resultado.engine,
        sifted_length=resultado.sifted_length,
        final_length=resultado.final_length,
        trace=traza,
        trace_truncated=resultado.is_truncated(),
    )

    resumen = resultado.summary()
    return {
        'success': True,
        'message': resultado.message,
        'session': session.to_dict(),
        # Traza real del protocolo, para que la vista dibuje lo que pasó
        # de verdad en lugar de inventar bits.
        'trace': traza,
        'simulation_details': {
            'key_length_initial': resumen['key_length_initial'],
            'key_length_after_sifting': resumen['key_length_after_sifting'],
            'key_length_final': resumen['key_length_final'],
            'matching_bases': resumen['matching_bases'],
            'error_rate': resumen['error_rate'],
            'noise_rate': resumen['noise_rate'],
            'eve_strategy': resumen['eve_strategy'],
            'eve_fraction': resumen['eve_fraction'],
            'engine': resumen['engine'],
        },
    }


def get_simulation_detail(session_id, user_id):
    """
    Devuelve una simulación con su traza, validando que sea del usuario.

    Regla de negocio: una sesión sólo la puede ver quien la ejecutó. La
    validación se hace acá y en la capa de datos, no en la vista.

    Args:
        session_id (int): ID de la sesión
        user_id (int): ID del usuario que la pide

    Returns:
        dict | None: {'session': ..., 'trace': ...} o None si no le pertenece
    """
    session = session_repository.get_user_session(session_id, user_id)
    if session is None:
        return None

    return {
        'session': session.to_dict(),
        'trace': session.trace.to_dict() if session.trace else None,
    }
