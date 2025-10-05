# app/models.py

from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

class SimulationSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_length = db.Column(db.Integer, nullable=False)
    has_eve = db.Column(db.Boolean, nullable=False)
    result = db.Column(db.String(50), nullable=False)
    final_key = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Session {self.id} for User {self.user_id}>'