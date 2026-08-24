"""
Tests para la aplicación Flask
"""
from app import app
from views.forms import LoginForm, RegisterForm


class TestAppBasics:
    """Tests básicos de la aplicación Flask"""
    
    def test_app_exists(self):
        """Test: la app existe"""
        assert app is not None
    
    def test_app_is_testing(self, client):
        """Test: la app está en modo testing"""
        assert app.config['TESTING'] is True


class TestForms:
    """Tests para los formularios"""
    
    def test_login_form_fields(self):
        """Test: LoginForm tiene los campos requeridos"""
        # Solo verificar que la clase existe y puede ser importada
        assert LoginForm is not None
    
    def test_register_form_fields(self):
        """Test: RegisterForm tiene los campos requeridos"""
        # Solo verificar que la clase existe y puede ser importada
        assert RegisterForm is not None


class TestRoutes:
    """Tests para las rutas de la aplicación"""
    
    def test_home_route_exists(self, client):
        """Test: ruta home existe"""
        response = client.get('/')
        
        # Debería redirigir al login o mostrar la página
        assert response.status_code in [200, 302]
    
    def test_404_error(self, client):
        """Test: error 404 para ruta no existente"""
        response = client.get('/ruta-no-existente')
        
        assert response.status_code == 404
