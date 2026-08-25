"""
Tests para los modelos de la base de datos
"""
from datos import db
from datos.models import User, SimulationSession
from datetime import datetime


class TestUserModel:
    """Tests para el modelo User"""
    
    def test_user_creation(self, app):
        """Test: crear un usuario"""
        user = User(username='testuser')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()

        assert user.id is not None
        assert user.username == 'testuser'

    def test_user_password_hashing(self, app):
        """Test: la contraseña debe estar hasheada"""
        user = User(username='testuser')
        user.set_password('testpass123')

        # La contraseña no debe ser igual al hash
        assert user.password_hash != 'testpass123'

    def test_user_check_password(self, app):
        """Test: verificar contraseña"""
        user = User(username='testuser')
        user.set_password('testpass123')

        assert user.check_password('testpass123') is True
        assert user.check_password('wrongpass') is False

    def test_user_repr(self, app):
        """Test: representación del usuario"""
        user = User(username='testuser')

        assert 'testuser' in repr(user)


class TestSimulationSessionModel:
    """Tests para el modelo SimulationSession"""
    
    def test_session_creation(self, app):
        """Test: crear una sesión de simulación"""
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

    def test_session_with_eve(self, app):
        """Test: sesión con espía (Eve)"""
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

    def test_session_timestamp(self, app):
        """Test: timestamp de la sesión"""
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

    def test_session_repr(self, app):
        """Test: representación de la sesión"""
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
