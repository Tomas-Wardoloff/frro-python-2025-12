"""
Formularios de la aplicación usando Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


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
    has_eve = BooleanField('Incluir espía (Eve)')
    submit = SubmitField('Ejecutar Simulación')
