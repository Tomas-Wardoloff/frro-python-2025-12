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


def run_bb84_simulation(user_id, key_length, has_eve):
    """
    Ejecuta la simulación completa del protocolo BB84 con Qiskit
    
    Args:
        user_id (int): ID del usuario que ejecuta la simulación
        key_length (int): Longitud de la clave inicial
        has_eve (bool): Si incluir un espía o no
    
    Returns:
        dict: Resultado de la simulación
    """
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
    
    try:
        # Importar la simulación BB84
        from business.bb84_simulation import simulate_bb84
        
        # Ejecutar la simulación cuántica
        sim_result = simulate_bb84(key_length, has_eve)
        
        if not sim_result['success']:
            return sim_result
        
        # Guardar en la base de datos
        session = session_repository.create_session(
            user_id=user_id,
            key_length=key_length,
            has_eve=has_eve,
            result=sim_result['result'],
            final_key=sim_result.get('final_key'),
            error_rate=sim_result.get('error_rate')
        )
        
        return {
            'success': True,
            'message': sim_result['message'],
            'session': session.to_dict(),
            'alice_bits': sim_result.get('alice_bits', []),
            'bob_bits': sim_result.get('bob_bits', []),
            'eve_bits': sim_result.get('eve_bits', []),
            'simulation_details': {
                'key_length_initial': sim_result.get('key_length_initial'),
                'key_length_after_sifting': sim_result.get('key_length_after_sifting'),
                'key_length_final': sim_result.get('key_length_final'),
                'matching_bases': sim_result.get('matching_bases'),
                'error_rate': sim_result.get('error_rate')
            }
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Error en la simulación: {str(e)}'
        }
