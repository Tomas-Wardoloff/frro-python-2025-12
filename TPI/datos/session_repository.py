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

    Nota: no filtra por usuario. Para lo que se muestra a un usuario concreto
    usar ``get_user_session``, que sí valida la propiedad.

    Args:
        session_id (int): ID de la sesión

    Returns:
        SimulationSession: La sesión encontrada o None
    """
    return db.session.get(SimulationSession, session_id)


def get_user_session(session_id, user_id):
    """
    Obtiene una sesión validando que pertenezca al usuario indicado.

    Evita que un usuario pueda leer las claves de otro cambiando el ID en la URL.

    Args:
        session_id (int): ID de la sesión
        user_id (int): ID del usuario que la pide

    Returns:
        SimulationSession: La sesión si es del usuario, None en cualquier otro caso
    """
    return db.session.execute(
        db.select(SimulationSession).filter_by(id=session_id, user_id=user_id)
    ).scalar_one_or_none()


def get_user_sessions(user_id, limit=None, offset=None):
    """
    Obtiene las sesiones de un usuario

    Args:
        user_id (int): ID del usuario
        limit (int, optional): Límite de resultados
        offset (int, optional): Desplazamiento, para paginar

    Returns:
        list: Lista de sesiones ordenadas por fecha descendente
    """
    query = (
        db.select(SimulationSession)
        .filter_by(user_id=user_id)
        .order_by(SimulationSession.timestamp.desc())
    )

    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    return list(db.session.execute(query).scalars())


def get_all_sessions(limit=None):
    """
    Obtiene todas las sesiones del sistema

    Args:
        limit (int, optional): Límite de resultados

    Returns:
        list: Lista de sesiones ordenadas por fecha descendente
    """
    query = db.select(SimulationSession).order_by(SimulationSession.timestamp.desc())

    if limit:
        query = query.limit(limit)

    return list(db.session.execute(query).scalars())


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
    return db.session.execute(
        db.select(db.func.count(SimulationSession.id)).filter_by(user_id=user_id)
    ).scalar_one()


def count_sessions_by_result(user_id):
    """
    Cuenta las sesiones de un usuario agrupadas por resultado.

    La agregación se hace en SQL: antes las estadísticas del dashboard traían
    todas las filas del usuario a memoria sólo para contarlas.

    Args:
        user_id (int): ID del usuario

    Returns:
        dict: {'secure': int, 'compromised': int, ...} con un cero por defecto
    """
    filas = db.session.execute(
        db.select(SimulationSession.result, db.func.count(SimulationSession.id))
        .filter_by(user_id=user_id)
        .group_by(SimulationSession.result)
    ).all()
    return {resultado: cantidad for resultado, cantidad in filas}


def get_error_rates(user_id):
    """
    Devuelve los QBER registrados de un usuario, del más viejo al más nuevo.

    Trae sólo la columna necesaria en vez de las entidades completas.

    Args:
        user_id (int): ID del usuario

    Returns:
        list: Lista de floats
    """
    return [
        tasa for tasa in db.session.execute(
            db.select(SimulationSession.error_rate)
            .filter_by(user_id=user_id)
            .order_by(SimulationSession.timestamp)
        ).scalars()
        if tasa is not None
    ]
