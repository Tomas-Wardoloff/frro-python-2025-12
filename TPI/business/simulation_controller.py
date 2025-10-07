"""
Capa de Negocio - Controlador de Simulación
Contiene la lógica de negocio del protocolo BB84
NO accede directamente a la base de datos, usa la capa de datos
"""
from datos import session_repository


def get_user_simulation_history(user_id, limit=10):
    """
    Obtiene el historial de simulaciones de un usuario
    
    Args:
        user_id (int): ID del usuario
        limit (int): Número máximo de resultados
    
    Returns:
        list: Lista de sesiones en formato diccionario
    """
    sessions = session_repository.get_user_sessions(user_id, limit)
    return [session.to_dict() for session in sessions]


def get_user_statistics(user_id):
    """
    Obtiene estadísticas de las simulaciones de un usuario
    Regla de negocio: Calcula métricas agregadas
    
    Args:
        user_id (int): ID del usuario
    
    Returns:
        dict: Estadísticas del usuario
    """
    sessions = session_repository.get_user_sessions(user_id)
    
    if not sessions:
        return {
            'total_simulations': 0,
            'secure_simulations': 0,
            'compromised_simulations': 0,
            'success_rate': 0.0
        }
    
    total = len(sessions)
    secure = sum(1 for s in sessions if s.result == 'secure')
    compromised = total - secure
    
    return {
        'total_simulations': total,
        'secure_simulations': secure,
        'compromised_simulations': compromised,
        'success_rate': round((secure / total) * 100, 2) if total > 0 else 0.0
    }


# TODO: Implementar la simulación del protocolo BB84
# Esta función será desarrollada en la siguiente fase
def run_bb84_simulation(user_id, key_length, has_eve):
    """
    Ejecuta la simulación completa del protocolo BB84
    Esta es la función principal que implementaremos en la siguiente fase
    
    Args:
        user_id (int): ID del usuario que ejecuta la simulación
        key_length (int): Longitud de la clave inicial
        has_eve (bool): Si incluir un espía o no
    
    Returns:
        dict: Resultado de la simulación
    """
    # Por ahora, retornamos un resultado simulado
    # TODO: Implementar la lógica real con Qiskit
    
    # Validaciones de negocio
    if key_length < 10:
        return {
            'success': False,
            'message': 'La longitud de la clave debe ser al menos 10 bits'
        }
    
    if key_length > 1000:
        return {
            'success': False,
            'message': 'La longitud de la clave no puede exceder 1000 bits'
        }
    
    # Simulación placeholder
    result = 'compromised' if has_eve else 'secure'
    final_key = '101010' if not has_eve else None
    error_rate = 0.25 if has_eve else 0.02
    
    # Guardar en la base de datos
    session = session_repository.create_session(
        user_id=user_id,
        key_length=key_length,
        has_eve=has_eve,
        result=result,
        final_key=final_key,
        error_rate=error_rate
    )
    
    return {
        'success': True,
        'message': 'Simulación completada',
        'session': session.to_dict()
    }
