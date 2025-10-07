"""
Capa de Datos - Repositorio de Sesiones de Simulación
Contiene todas las operaciones de acceso a datos relacionadas con sesiones
"""
from datos.models import SimulationSession, db


def create_session(user_id, key_length, has_eve, result, final_key=None, error_rate=None):
    """
    Crea una nueva sesión de simulación en la base de datos
    
    Args:
        user_id (int): ID del usuario que ejecuta la simulación
        key_length (int): Longitud de la clave inicial
        has_eve (bool): Si hay espía o no
        result (str): Resultado de la simulación ('secure' o 'compromised')
        final_key (str, optional): La clave final generada
        error_rate (float, optional): Tasa de error cuántico
    
    Returns:
        SimulationSession: La sesión creada
    """
    session = SimulationSession(
        user_id=user_id,
        key_length=key_length,
        has_eve=has_eve,
        result=result,
        final_key=final_key,
        error_rate=error_rate
    )
    db.session.add(session)
    db.session.commit()
    return session


def get_session_by_id(session_id):
    """
    Obtiene una sesión por su ID
    
    Args:
        session_id (int): ID de la sesión
    
    Returns:
        SimulationSession: La sesión encontrada o None
    """
    return SimulationSession.query.get(session_id)


def get_user_sessions(user_id, limit=None):
    """
    Obtiene todas las sesiones de un usuario
    
    Args:
        user_id (int): ID del usuario
        limit (int, optional): Límite de resultados
    
    Returns:
        list: Lista de sesiones ordenadas por fecha descendente
    """
    query = SimulationSession.query.filter_by(user_id=user_id).order_by(
        SimulationSession.timestamp.desc()
    )
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def get_all_sessions(limit=None):
    """
    Obtiene todas las sesiones del sistema
    
    Args:
        limit (int, optional): Límite de resultados
    
    Returns:
        list: Lista de sesiones ordenadas por fecha descendente
    """
    query = SimulationSession.query.order_by(SimulationSession.timestamp.desc())
    
    if limit:
        query = query.limit(limit)
    
    return query.all()


def delete_session(session_id):
    """
    Elimina una sesión de la base de datos
    
    Args:
        session_id (int): ID de la sesión a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False si no existe
    """
    session = get_session_by_id(session_id)
    if session:
        db.session.delete(session)
        db.session.commit()
        return True
    return False


def count_user_sessions(user_id):
    """
    Cuenta el número total de sesiones de un usuario
    
    Args:
        user_id (int): ID del usuario
    
    Returns:
        int: Número de sesiones
    """
    return SimulationSession.query.filter_by(user_id=user_id).count()
