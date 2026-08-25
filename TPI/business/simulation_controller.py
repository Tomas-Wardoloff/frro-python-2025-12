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


def delete_user_session(session_id, user_id):
    """
    Borra una simulación, validando que sea del usuario que la pide.

    Regla de negocio: nadie puede borrar una sesión ajena. Se resuelve
    buscándola con el filtro de dueño antes de borrar.

    Args:
        session_id (int): ID de la sesión
        user_id (int): ID del usuario que pide el borrado

    Returns:
        bool: True si se borró, False si no existía o no le pertenecía
    """
    session = session_repository.get_user_session(session_id, user_id)
    if session is None:
        return False
    return session_repository.delete_session(session_id)


def get_paginated_history(user_id, pagina=1, por_pagina=20):
    """
    Historial paginado.

    Antes el historial tenía un tope duro de 50 sin forma de ver el resto.

    Args:
        user_id (int): ID del usuario
        pagina (int): Número de página, empezando en 1
        por_pagina (int): Filas por página

    Returns:
        dict: sesiones de la página más los datos de navegación
    """
    pagina = max(1, int(pagina or 1))
    por_pagina = min(max(1, int(por_pagina or 20)), 100)

    total = session_repository.count_user_sessions(user_id)
    total_paginas = max(1, -(-total // por_pagina))  # división hacia arriba
    pagina = min(pagina, total_paginas)

    sesiones = session_repository.get_user_sessions(
        user_id, limit=por_pagina, offset=(pagina - 1) * por_pagina
    )

    return {
        'sesiones': [s.to_dict() for s in sesiones],
        'pagina': pagina,
        'total_paginas': total_paginas,
        'total': total,
        'hay_anterior': pagina > 1,
        'hay_siguiente': pagina < total_paginas,
    }


# Cortes del histograma de QBER, en porcentaje
BUCKETS_QBER = [0, 5, 11, 20, 30, 101]


def get_user_analytics(user_id):
    """
    Series agregadas para los gráficos del dashboard.

    Args:
        user_id (int): ID del usuario

    Returns:
        dict: datos listos para graficar
    """
    sesiones = session_repository.get_user_sessions(user_id)

    # Histograma de QBER
    etiquetas, cuentas = [], []
    for i in range(len(BUCKETS_QBER) - 1):
        desde, hasta = BUCKETS_QBER[i], BUCKETS_QBER[i + 1]
        etiquetas.append(f'{desde}–{hasta}%' if hasta <= 100 else f'{desde}%+')
        cuentas.append(0)

    for s in sesiones:
        pct = (s.error_rate or 0) * 100
        for i in range(len(BUCKETS_QBER) - 1):
            if BUCKETS_QBER[i] <= pct < BUCKETS_QBER[i + 1]:
                cuentas[i] += 1
                break

    # Evolución cronológica del QBER, separando corridas con y sin espía
    cronologia = sorted(sesiones, key=lambda x: x.timestamp)
    serie = [
        {
            'id': s.id,
            'qber': round((s.error_rate or 0) * 100, 2),
            'con_espia': bool(s.has_eve),
            'ruido': round((s.noise_rate or 0) * 100, 1),
            'resultado': s.result,
        }
        for s in cronologia
    ]

    return {
        'histograma': {'etiquetas': etiquetas, 'cuentas': cuentas},
        'serie': serie,
        'umbral': 11.0,
    }


def reconstruir_clave_de_eve(traza):
    """
    Arma la clave que Eve creería tener, a partir de la traza guardada.

    Sigue el mismo camino que la clave real: se toman los qubits cuyas bases
    coincidieron y se descartan los que se revelaron en la verificación. Donde
    Eve no interceptó se pone ``'?'``, porque simplemente no tiene ese bit.

    Devuelve None si la traza no alcanza (en corridas largas se guarda recortada,
    con lo que no cubre toda la clave).

    Args:
        traza (dict): la traza persistida de la simulación

    Returns:
        str | None: la clave parcial de Eve
    """
    if not traza:
        return None

    en_muestra = set(traza.get('sample_positions', []))
    eve_bits = traza.get('eve_bits', [])

    clave = []
    for posicion, indice in enumerate(traza.get('sifted_indices', [])):
        if posicion in en_muestra:
            continue
        if indice >= len(eve_bits):
            return None
        bit = eve_bits[indice]
        clave.append('?' if bit < 0 else str(bit))

    return ''.join(clave) if clave else None
