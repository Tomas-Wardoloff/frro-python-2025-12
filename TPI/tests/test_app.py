"""
Tests para la aplicación Flask
"""
from views.forms import LoginForm, RegisterForm


class TestAppBasics:
    """Tests básicos de la aplicación Flask"""
    
    def test_la_app_se_construye(self, app):
        """La factory devuelve una aplicación utilizable."""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_los_tests_no_usan_un_archivo_de_base(self, app):
        """Red de seguridad: la suite nunca debe tocar la base de desarrollo."""
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        assert 'qsec.db' not in uri, f'los tests apuntan a la base real: {uri}'


class TestForms:
    """Tests para los formularios"""
    
    def test_login_form_tiene_sus_campos(self, app):
        """Antes esto sólo comprobaba que la clase se pudiera importar."""
        with app.test_request_context():
            campos = set(LoginForm()._fields)
        assert {'username', 'password', 'remember_me'} <= campos

    def test_register_form_tiene_sus_campos(self, app):
        with app.test_request_context():
            campos = set(RegisterForm()._fields)
        assert {'username', 'password'} <= campos


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
