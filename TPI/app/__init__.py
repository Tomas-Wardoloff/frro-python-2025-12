# app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Creamos la aplicación Flask
app = Flask(__name__)

# Configuramos la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qsec.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Creamos el objeto de la base de datos
db = SQLAlchemy(app)

# Al final del archivo, importamos los modelos para que SQLAlchemy los conozca
# Lo pondremos aquí para evitar importaciones circulares
from app import models