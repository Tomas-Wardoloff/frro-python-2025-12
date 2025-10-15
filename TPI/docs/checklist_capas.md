# Checklist Sobre el Diseño en Capas

El siguiente checklist permite una fácil detección de malas prácticas y posibles correcciones para implementar el patrón de diseño en capas.

## Checklist

### General

- [ ] El sistema debe estar **DESPLEGADO**
    - [ ] Debe estar online y accesible desde cualquier dispositivo, es decir no desde localhost (Sólo para Web)
    - [ ] En caso de no ser Web, debe poder installarse desde PyPi usando pip install
- [X] Cada capa debe seguir las buenas prácticas de formato
    - [X] En caso de ser un único archivo el archivo deberá tener el nombre de la capa (db.py, controller.py, presentation.py)
    - [X] En caso de tener varios archivos para una misma capa, deben estar todos dentro de una carpeta con el nombre correspondiente
    - [X] Cualquiera sea el caso, debe haber un archivo app.py en la raiz que será el que deberá ejecutar la aplicación.

### Presentación (Flask, Django, Kivy, etc.)

- [X] **NO** se utiliza ninguna función, objeto o clase de la capa de Datos.
- [X] Toda la lógica de los elementos interactivos (botones, menúes, etc.) se ejecuta mediante una función en la capa de negocio y **NO** dentro de elementos de interfaz.
- [X] Esta capa funciona aunque se modifique cualquier archivo de la capa de datos.
- [X] Debe cumplir con los estándares de formato:
    - Si es un único archivo, debe llamarse **views.py**
    - Si son múltiples archivos, deben estar todos en una carpeta **views**

### Negocio

- [X] Ninguna función realiza llamadas a la base de datos directamente ni con ORM, todas deben llamar a una función de la capa de datos.
- [X] Ninguna función involucra elementos específicos de interfaz (Botones, HTML, etc.).
- [X] Esta capa seguiría funcionando si se cambiara el motor de base de datos.
- [X] Todas las funciones devuelven objetos de Negocio (Usuario, Reserva, Turno, etc.).
- [X] Se debe validar al menos una regla de negocio
- [X] Debe cumplir con los estándares de formato:
    - Si es un único archivo, debe llamarse **controller.py**
    - Si son múltiples archivos, deben estar todos en una carpeta **business** o **controller**

### Datos

- [X] Todas las funciones devuelven objetos de Negocio (Usuario, Reserva, Turno, etc.).
- [X] Todas las consultas a la base de datos se hacen desde esta capa.
- [X] Solo se acceden a las funciones de esta capa desde la Capa de Negocio
- [X] Se utiliza una base de datos (MySQL, Mongo, SQLite)
- [X] Se encuentra disponible el Modelo de Dominio / Diagrama Entidad Relación (Usar https://draw.io/) o similar
- [X] Debe cumplir con los estándares de formato:
    - Si es un único archivo, debe llamarse **db.py**
    - Si son múltiples archivos, deben estar todos en una carpeta **datos**
