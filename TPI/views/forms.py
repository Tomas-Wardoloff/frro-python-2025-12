"""
Formularios de la aplicación usando Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange

from business.bb84 import EVE_INTERCEPT_RESEND, EVE_NINGUNA, motores_disponibles


class RegisterForm(FlaskForm):
    """Formulario de registro de usuario"""
    username = StringField(
        'Usuario',
        validators=[
            DataRequired(message='El usuario es obligatorio'),
            Length(min=3, max=80, message='El usuario debe tener entre 3 y 80 caracteres')
        ]
    )
    password = PasswordField(
        'Contraseña',
        validators=[
            DataRequired(message='La contraseña es obligatoria'),
            Length(min=6, message='La contraseña debe tener al menos 6 caracteres')
        ]
    )
    submit = SubmitField('Registrarse')


class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    username = StringField(
        'Usuario',
        validators=[DataRequired(message='El usuario es obligatorio')]
    )
    password = PasswordField(
        'Contraseña',
        validators=[DataRequired(message='La contraseña es obligatoria')]
    )
    remember_me = BooleanField('Recordarme')
    submit = SubmitField('Iniciar Sesión')


def _opciones_de_motor():
    """Motores disponibles en este entorno, para el desplegable."""
    etiquetas = {
        'analytic': 'Analítico (rápido)',
        'qiskit': 'Qiskit — circuitos cuánticos',
    }
    return [(m, etiquetas.get(m, m)) for m in motores_disponibles()]


class SimulationForm(FlaskForm):
    """Formulario para configurar una simulación BB84"""

    key_length = IntegerField(
        'Longitud de la clave',
        validators=[
            DataRequired(message='La longitud es obligatoria'),
            NumberRange(min=10, max=1000, message='La longitud debe estar entre 10 y 1000 bits')
        ],
        default=64
    )

    # Ojo: InputRequired y no DataRequired. DataRequired considera el 0 como
    # ausencia de dato, con lo que "sin ruido" y "sin interceptación" —los
    # valores por defecto— serían rechazados por el validador.
    noise_rate = IntegerField(
        'Ruido del canal (%)',
        validators=[
            InputRequired(message='Indicá el ruido del canal'),
            NumberRange(min=0, max=50, message='El ruido debe estar entre 0% y 50%')
        ],
        default=0
    )

    eve_strategy = SelectField(
        'Estrategia del espía',
        choices=[
            (EVE_NINGUNA, 'Sin espía'),
            (EVE_INTERCEPT_RESEND, 'Eve intercepta y reenvía'),
        ],
        default=EVE_NINGUNA
    )

    eve_fraction = IntegerField(
        'Qubits interceptados (%)',
        validators=[
            InputRequired(message='Indicá la fracción interceptada'),
            NumberRange(min=0, max=100, message='La fracción debe estar entre 0% y 100%')
        ],
        default=100
    )

    engine = SelectField(
        'Motor de simulación',
        choices=_opciones_de_motor,
        default='analytic'
    )

    submit = SubmitField('Ejecutar Simulación')
