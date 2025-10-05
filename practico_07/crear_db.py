# crear_db.py

# Importamos la 'Base' que contiene los metadatos de nuestras tablas (los planos)
from practico_05.ejercicio_01 import Base

# NO PODEMOS importar el engine directamente, así que importamos la clase que lo crea.
from practico_05.ejercicio_02 import DatosSocio

print("Iniciando creación de la base de datos...")
print("Esta versión respeta la estructura original de los prácticos anteriores.")

# Paso 1: Crear una instancia de la capa de datos.
# Al hacer esto, el __init__ de DatosSocio se ejecuta y crea el self.engine.
# Aunque no lo usaremos para nada más, este paso es crucial para tener el engine.
print("Creando una instancia temporal de DatosSocio para acceder al engine...")
instancia_datos = DatosSocio()

# Paso 2: Acceder al engine a través de la instancia que acabamos de crear.
# El engine está guardado como un atributo del objeto.
engine_obtenido = instancia_datos.engine

# Paso 3: Usar el engine obtenido para crear las tablas.
# Esta es la línea mágica que usa los "planos" (Base.metadata) y la
# "conexión a la obra" (engine_obtenido) para construir las tablas.
try:
    Base.metadata.create_all(engine_obtenido)
    print("Base de datos y tablas creadas (o ya existentes) con éxito.")
except Exception as e:
    print(f"Ocurrió un error al intentar crear las tablas: {e}")
    print("Asegúrate de que la clase 'DatosSocio' tiene un atributo 'self.engine'.")