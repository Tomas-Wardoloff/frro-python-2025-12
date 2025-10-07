"""
Capa de Datos - Repositorio de Usuarios
Contiene todas las operaciones de acceso a datos relacionadas con usuarios
"""
from datos.models import User, db


def create_user(username, password):
    """
    Crea un nuevo usuario en la base de datos
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano (será hasheada)
    
    Returns:
        User: El usuario creado o None si ya existe
    """
    # Validar que no exista el usuario
    existing_user = get_user_by_username(username)
    if existing_user:
        return None
    
    # Crear nuevo usuario
    new_user = User()
    new_user.username = username
    new_user.set_password(password)
    
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_user_by_id(user_id):
    """
    Obtiene un usuario por su ID
    
    Args:
        user_id (int): ID del usuario
    
    Returns:
        User: El usuario encontrado o None
    """
    return User.query.get(user_id)


def get_user_by_username(username):
    """
    Obtiene un usuario por su nombre de usuario
    
    Args:
        username (str): Nombre de usuario
    
    Returns:
        User: El usuario encontrado o None
    """
    return User.query.filter_by(username=username).first()


def verify_user_password(username, password):
    """
    Verifica las credenciales de un usuario
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña en texto plano
    
    Returns:
        User: El usuario si las credenciales son correctas, None si no
    """
    user = get_user_by_username(username)
    if user and user.check_password(password):
        return user
    return None


def get_all_users():
    """
    Obtiene todos los usuarios (útil para admin)
    
    Returns:
        list: Lista de usuarios
    """
    return User.query.all()


def delete_user(user_id):
    """
    Elimina un usuario de la base de datos
    
    Args:
        user_id (int): ID del usuario a eliminar
    
    Returns:
        bool: True si se eliminó correctamente, False si no existe
    """
    user = get_user_by_id(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return True
    return False
