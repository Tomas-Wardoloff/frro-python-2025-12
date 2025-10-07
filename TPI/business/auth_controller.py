"""
Capa de Negocio - Controlador de Autenticación
Contiene la lógica de negocio relacionada con usuarios y autenticación
NO accede directamente a la base de datos, usa la capa de datos
"""
from datos import user_repository


def register_user(username, password):
    """
    Registra un nuevo usuario en el sistema
    Regla de negocio: El username debe ser único
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña
    
    Returns:
        dict: Resultado de la operación con 'success' y 'message'
    """
    # Validaciones de negocio
    if not username or len(username) < 3:
        return {
            'success': False,
            'message': 'El nombre de usuario debe tener al menos 3 caracteres'
        }
    
    if not password or len(password) < 6:
        return {
            'success': False,
            'message': 'La contraseña debe tener al menos 6 caracteres'
        }
    
    # Intentar crear el usuario
    user = user_repository.create_user(username, password)
    
    if user:
        return {
            'success': True,
            'message': 'Usuario registrado exitosamente',
            'user': user
        }
    else:
        return {
            'success': False,
            'message': f'El nombre de usuario "{username}" ya está en uso'
        }


def authenticate_user(username, password):
    """
    Autentica un usuario verificando sus credenciales
    
    Args:
        username (str): Nombre de usuario
        password (str): Contraseña
    
    Returns:
        dict: Resultado de la operación con 'success', 'message' y 'user'
    """
    # Validaciones básicas
    if not username or not password:
        return {
            'success': False,
            'message': 'Debe proporcionar usuario y contraseña'
        }
    
    # Verificar credenciales
    user = user_repository.verify_user_password(username, password)
    
    if user:
        return {
            'success': True,
            'message': 'Autenticación exitosa',
            'user': user
        }
    else:
        return {
            'success': False,
            'message': 'Usuario o contraseña incorrectos'
        }


def get_user_info(user_id):
    """
    Obtiene la información de un usuario
    
    Args:
        user_id (int): ID del usuario
    
    Returns:
        dict: Información del usuario o None
    """
    user = user_repository.get_user_by_id(user_id)
    
    if user:
        return {
            'id': user.id,
            'username': user.username,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return None


def get_user_by_username(username):
    """
    Obtiene un usuario por su nombre de usuario
    
    Args:
        username (str): Nombre de usuario
    
    Returns:
        User: El usuario o None
    """
    return user_repository.get_user_by_username(username)
