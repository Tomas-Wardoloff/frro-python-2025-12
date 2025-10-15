"""
Tests de integración para el TPI
"""
import pytest
import sys
import os

# Agregar el directorio TPI al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from datos.models import User, SimulationSession


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


class TestUserFlow:
    """Tests del flujo de usuario"""
    
    def test_user_can_register(self, client):
        """Test: un usuario puede registrarse"""
        with app.app_context():
            # Crear un usuario
            user = User(username='newuser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Verificar que se creó
            found_user = User.query.filter_by(username='newuser').first()
            assert found_user is not None
            assert found_user.username == 'newuser'
    
    def test_user_can_authenticate(self, client):
        """Test: un usuario puede autenticarse"""
        with app.app_context():
            # Crear un usuario
            user = User(username='testuser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Verificar autenticación
            found_user = User.query.filter_by(username='testuser').first()
            assert found_user is not None
            assert found_user.check_password('password123')
            assert not found_user.check_password('wrongpassword')
    
    def test_user_can_simulate(self, client):
        """Test: un usuario puede simular"""
        with app.app_context():
            # Crear un usuario
            user = User(username='simulator')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Crear una sesión de simulación
            session = SimulationSession(
                key_length=256,
                has_eve=False,
                result='secure',
                final_key='01101010101010101010',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            # Verificar que se creó la sesión
            found_session = SimulationSession.query.filter_by(user_id=user.id).first()
            assert found_session is not None
            assert found_session.key_length == 256
            assert found_session.result == 'secure'
    
    def test_user_can_view_history(self, client):
        """Test: un usuario puede ver su historial"""
        with app.app_context():
            # Crear un usuario
            user = User(username='historian')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Crear múltiples sesiones
            for i in range(3):
                session = SimulationSession(
                    key_length=256 + i,
                    has_eve=(i % 2 == 0),
                    result='secure' if i % 2 == 0 else 'compromised',
                    user_id=user.id
                )
                db.session.add(session)
            db.session.commit()
            
            # Verificar historial
            sessions = SimulationSession.query.filter_by(user_id=user.id).all()
            assert len(sessions) == 3


class TestBB84Integration:
    """Tests de integración con BB84"""
    
    def test_bb84_simulation_recorded(self, client):
        """Test: resultados de BB84 se registran"""
        with app.app_context():
            # Crear usuario
            user = User(username='bb84user')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Simular y guardar
            session = SimulationSession(
                key_length=128,
                has_eve=True,
                result='compromised',
                final_key='10101010',
                user_id=user.id
            )
            db.session.add(session)
            db.session.commit()
            
            # Verificar que se guardó correctamente
            saved_session = SimulationSession.query.filter_by(
                user_id=user.id,
                has_eve=True
            ).first()
            assert saved_session is not None
            assert saved_session.result == 'compromised'
            assert saved_session.final_key == '10101010'
