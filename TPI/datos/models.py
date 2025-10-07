"""
Modelos de la Base de Datos
Representan las entidades del dominio
"""
from datos import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """
    Modelo de Usuario
    Representa a un usuario registrado en el sistema
    """
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # Relación con sesiones de simulación
    sessions = db.relationship('SimulationSession', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """Hashea y guarda la contraseña"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica si la contraseña es correcta"""
        return check_password_hash(self.password_hash, password)


class SimulationSession(db.Model):
    """
    Modelo de Sesión de Simulación
    Almacena el resultado de cada simulación del protocolo BB84
    """
    __tablename__ = 'simulation_session'
    
    id = db.Column(db.Integer, primary_key=True)
    key_length = db.Column(db.Integer, nullable=False)
    has_eve = db.Column(db.Boolean, nullable=False, default=False)
    result = db.Column(db.String(50), nullable=False)  # 'secure' o 'compromised'
    final_key = db.Column(db.Text, nullable=True)
    error_rate = db.Column(db.Float, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<SimulationSession {self.id} - {self.result}>"
    
    def to_dict(self):
        """Convierte la sesión a diccionario para facilitar el uso"""
        return {
            'id': self.id,
            'key_length': self.key_length,
            'has_eve': self.has_eve,
            'result': self.result,
            'final_key': self.final_key,
            'error_rate': self.error_rate,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'user_id': self.user_id
        }
