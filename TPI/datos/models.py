"""
Modelos de la Base de Datos
Representan las entidades del dominio
"""
import json
from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from datos import db


def utc_now():
    """Devuelve el instante actual en UTC (timezone-aware).

    Reemplaza a ``datetime.utcnow``, deprecada desde Python 3.12, que además
    devolvía un datetime naive (sin zona horaria).
    """
    return datetime.now(timezone.utc)


class User(db.Model, UserMixin):
    """
    Modelo de Usuario
    Representa a un usuario registrado en el sistema
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    # 255 y no 128: el hash scrypt por defecto de Werkzeug ocupa ~162 caracteres.
    # SQLite ignora la longitud declarada, pero Postgres/MySQL la validan y el
    # registro de usuarios fallaría en produccion.
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True, default=utc_now)

    # Relación con sesiones de simulación
    sessions = db.relationship(
        'SimulationSession',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

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
    timestamp = db.Column(db.DateTime, nullable=False, default=utc_now, index=True)

    # Parámetros del canal y del ataque
    noise_rate = db.Column(db.Float, nullable=True, default=0.0)
    eve_strategy = db.Column(db.String(30), nullable=True, default='none')
    eve_fraction = db.Column(db.Float, nullable=True, default=0.0)
    engine = db.Column(db.String(20), nullable=True, default='analytic')

    # Métricas del cribado, para no recalcularlas al listar el historial
    sifted_length = db.Column(db.Integer, nullable=True)
    final_length = db.Column(db.Integer, nullable=True)

    # Foreign Key
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    trace = db.relationship(
        'SimulationTrace',
        backref='session',
        uselist=False,
        cascade='all, delete-orphan'
    )

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
            'noise_rate': self.noise_rate or 0.0,
            'eve_strategy': self.eve_strategy or 'none',
            'eve_fraction': self.eve_fraction or 0.0,
            'engine': self.engine or 'analytic',
            'sifted_length': self.sifted_length,
            'final_length': self.final_length,
            'user_id': self.user_id
        }


class SimulationTrace(db.Model):
    """
    Traza bit a bit de una simulación.

    Vive en una tabla aparte (1:1 con SimulationSession) y se carga sólo cuando
    se pide, para que listar el historial no tenga que traer los blobs JSON.
    """
    __tablename__ = 'simulation_trace'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey('simulation_session.id'),
        nullable=False,
        unique=True,
        index=True
    )
    # JSON con las listas del protocolo, recortadas a MAX_TRACE_BITS
    payload = db.Column(db.Text, nullable=False)
    truncated = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<SimulationTrace session={self.session_id}>"

    def to_dict(self):
        """Devuelve la traza deserializada."""
        datos = json.loads(self.payload)
        datos['truncated'] = self.truncated
        return datos
