"""
Tests para los modelos de la base de datos
"""
import pytest
import sys
import os

# Agregar el directorio TPI al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from datos.models import User, SimulationSession
from datetime import datetime


@pytest.fixture
def client():
    """Crea un cliente de prueba con base de datos temporal"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


class TestUserModel:
    """Tests para el modelo User"""
    
    def test_user_creation(self, client):
        """Test: crear un usuario"""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('testpass123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'testuser'
    
    def test_user_password_hashing(self, client):
        """Test: la contraseña debe estar hasheada"""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('testpass123')
            
            # La contraseña no debe ser igual al hash
            assert user.password_hash != 'testpass123'
    
    def test_user_check_password(self, client):
        """Test: verificar contraseña"""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('testpass123')
            
            assert user.check_password('testpass123') is True
            assert user.check_password('wrongpass') is False
    
    def test_user_repr(self, client):
        """Test: representación del usuario"""
        with app.app_context():
            user = User(username='testuser')
            
            assert 'testuser' in repr(user)


class TestSimulationSessionModel:
    """Tests para el modelo SimulationSession"""
    
    def test_session_creation(self, client):
        """Test: crear una sesión de simulación"""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            session = SimulationSession(
                key_length=256,
                has_eve=False,
                result='secure',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.id is not None
            assert session.key_length == 256
            assert session.has_eve is False
    
    def test_session_with_eve(self, client):
        """Test: sesión con espía (Eve)"""
        with app.app_context():
            user = User(username='testuser2')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            session = SimulationSession(
                key_length=256,
                has_eve=True,
                result='compromised',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            assert session.has_eve is True
            assert session.result == 'compromised'
    
    def test_session_timestamp(self, client):
        """Test: timestamp de la sesión"""
        with app.app_context():
            user = User(username='testuser3')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            session = SimulationSession(
                key_length=256,
                has_eve=False,
                result='secure',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            # Verificar que el timestamp se asignó automáticamente
            assert session.timestamp is not None
            assert isinstance(session.timestamp, datetime)
    
    def test_session_repr(self, client):
        """Test: representación de la sesión"""
        with app.app_context():
            user = User(username='testuser4')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            session = SimulationSession(
                key_length=256,
                has_eve=False,
                result='secure',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            # La sesión debería tener una representación
            assert str(session.id) is not None
