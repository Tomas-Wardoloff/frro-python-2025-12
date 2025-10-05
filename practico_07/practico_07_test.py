# Tests para el Práctico 07 - Aplicación Flask

import unittest
import os
import sys

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from practico_07.app import app
from practico_06.capa_negocio import NegocioSocio
from practico_05.ejercicio_01 import Socio


class TestFlaskApp(unittest.TestCase):

    def setUp(self):
        """Configurar el cliente de prueba de Flask"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.negocio = NegocioSocio()
        # Limpiar la base de datos antes de cada test
        self.negocio.datos.borrar_todos()

    def tearDown(self):
        """Limpiar la base de datos después de cada test"""
        self.negocio.datos.borrar_todos()

    def test_index_route_exists(self):
        """Test que la ruta principal existe y devuelve 200"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_index_shows_socios(self):
        """Test que la página principal muestra los socios"""
        # Agregar un socio de prueba usando la ruta de alta
        self.client.post('/alta', data={
            'dni': '12345678',
            'nombre': 'Juan',
            'apellido': 'Perez'
        })

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Juan', response.data)
        self.assertIn(b'Perez', response.data)

    def test_alta_route_get(self):
        """Test que la ruta de alta existe y devuelve el formulario"""
        response = self.client.get('/alta')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alta de Socio', response.data)

    def test_alta_route_post(self):
        """Test que se puede dar de alta un socio mediante POST"""
        response = self.client.post('/alta', data={
            'dni': '87654321',
            'nombre': 'Maria',
            'apellido': 'Garcia'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Maria', response.data)
        self.assertIn(b'Garcia', response.data)

    def test_app_has_secret_key(self):
        """Test que la aplicación tiene una clave secreta configurada"""
        self.assertIsNotNone(self.app.secret_key)

    def test_templates_exist(self):
        """Test que los archivos de template existen"""
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.assertTrue(os.path.exists(os.path.join(template_dir, 'index.html')))
        self.assertTrue(os.path.exists(os.path.join(template_dir, 'form_socio.html')))
        self.assertTrue(os.path.exists(os.path.join(template_dir, 'layout.html')))


if __name__ == '__main__':
    unittest.main()
