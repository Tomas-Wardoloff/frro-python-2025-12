import os
from flask import Flask, render_template, request, redirect, url_for, flash
from practico_06.capa_negocio import NegocioSocio, DniRepetido, LongitudInvalida, MaximoAlcanzado
from practico_05.ejercicio_01 import Socio

# --- !! SOLUCIÓN DEFINITIVA PARA RUTAS RELATIVAS !! ---
# Este bloque asegura que el directorio de trabajo (CWD) sea siempre la raíz del proyecto,
# para que la ruta relativa 'sqlite:///socios.db' se resuelva siempre en el mismo lugar.

# 1. Obtener la ruta absoluta del directorio donde está este script (app.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Obtener la ruta del directorio padre (que es la raíz del proyecto)
project_root = os.path.dirname(script_dir)

# 3. Cambiar el Directorio de Trabajo Actual a la raíz del proyecto
os.chdir(project_root)

# (Opcional) Imprimir un mensaje para verificar que el cambio se hizo correctamente
print(f"Directorio de trabajo cambiado a: {os.getcwd()}")

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
# Se necesita una clave secreta para poder usar los mensajes 'flash'
app.secret_key = 'una_clave_muy_secreta'

# --- Instancia de la Capa de Negocio ---
# Creamos una única instancia que usará toda la aplicación
negocio = NegocioSocio()


# --- RUTAS DE LA APLICACIÓN ---


@app.route('/')
def index():
    """Página principal que muestra la lista de todos los socios."""
    try:
        # Pedimos a la capa de negocio que nos de todos los socios
        todos_los_socios = negocio.todos()
        # Le pasamos la lista de socios a la plantilla HTML
        return render_template('index.html', socios=todos_los_socios)
    except Exception as e:
        flash(f"Error al cargar los socios: {e}", "danger")
        return render_template('index.html', socios=[])


@app.route('/alta', methods=['GET', 'POST'])
def alta_socio():
    """Página para dar de alta un nuevo socio."""
    if request.method == 'POST':
        # Si el método es POST, significa que el usuario envió el formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']

        # Creamos el objeto socio (sin id, la BD se lo asignará)
        nuevo_socio = Socio(id=None, nombre=nombre, apellido=apellido, dni=dni)

        try:
            # Intentamos darlo de alta usando la capa de negocio
            negocio.alta(nuevo_socio)
            # Si tiene éxito, mostramos un mensaje y redirigimos a la página principal
            flash('Socio dado de alta con éxito!', 'success')
            return redirect(url_for('index'))
        except (DniRepetido, LongitudInvalida, MaximoAlcanzado) as e:
            # Si la capa de negocio lanza una excepción, la mostramos como un error
            flash(f'Error al dar de alta el socio: {e}', 'danger')
            # Volvemos a mostrar el formulario, pero con los datos que ya había escrito
            return render_template('form_socio.html', titulo='Alta de Socio', socio=nuevo_socio)

    # Si el método es GET, simplemente mostramos el formulario de alta vacío
    return render_template('form_socio.html', titulo='Alta de Socio')


@app.route('/baja', methods=['POST'])
def baja_socio():
    """Ruta para procesar la baja de un socio."""
    try:
        id_socio_a_borrar = request.form['id_socio']
        # Le pedimos a la capa de negocio que borre el socio
        negocio.baja(int(id_socio_a_borrar))
        flash('Socio dado de baja con éxito.', 'success')
    except KeyError:
        flash('Debe seleccionar un socio para dar de baja.', 'warning')
    except Exception as e:
        flash(f'Error al dar de baja el socio: {e}', 'danger')

    return redirect(url_for('index'))


@app.route('/modificar/<int:id_socio>', methods=['GET', 'POST'])
def modificar_socio(id_socio):
    """Página para modificar los datos de un socio existente."""
    # Buscamos el socio para tener sus datos
    socio_a_modificar = negocio.buscar(id_socio)

    if socio_a_modificar is None:
        flash('Socio no encontrado.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Si el usuario envía el formulario de modificación
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        dni = request.form['dni']

        # Creamos el objeto con los datos nuevos y el ID original
        socio_modificado = Socio(id=id_socio, nombre=nombre, apellido=apellido, dni=dni)

        try:
            # Intentamos la modificación a través de la capa de negocio
            negocio.modificacion(socio_modificado)
            flash('Socio modificado con éxito!', 'success')
            return redirect(url_for('index'))
        except (LongitudInvalida, DniRepetido) as e:
            # Si hay un error, lo mostramos
            flash(f'Error al modificar el socio: {e}', 'danger')
            # Volvemos a mostrar el formulario con los datos incorrectos para que los corrija
            return render_template('form_socio.html', titulo='Modificar Socio', socio=socio_modificado)

    # Si es GET, mostramos el formulario con los datos actuales del socio
    return render_template('form_socio.html', titulo='Modificar Socio', socio=socio_a_modificar)


@app.route('/seleccionar_accion', methods=['POST'])
def seleccionar_accion():
    """Ruta intermedia para decidir si se va a modificar o a dar de baja."""
    try:
        id_socio_seleccionado = request.form['id_socio']
        if 'modificar' in request.form:
            return redirect(url_for('modificar_socio', id_socio=id_socio_seleccionado))
        elif 'baja' in request.form:
            # Para la baja, usamos un formulario separado para confirmación
            # o lo procesamos directamente. Por simplicidad, lo procesamos.
            negocio.baja(int(id_socio_seleccionado))
            flash('Socio dado de baja con éxito.', 'success')
    except KeyError:
        flash('Por favor, seleccione un socio para realizar una acción.', 'warning')
    except Exception as e:
        flash(f'Ocurrió un error: {e}', 'danger')

    return redirect(url_for('index'))


# --- Iniciar la Aplicación ---
if __name__ == '__main__':
    # El modo debug permite ver los cambios sin tener que reiniciar el servidor
    app.run(debug=True)
