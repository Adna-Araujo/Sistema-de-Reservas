from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime

# -------------------------
# Usuário
# -------------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    reservas = db.relationship('Reserva', backref='autor', lazy=True)

    def __repr__(self):
        return f"Usuario('{self.username}', '{self.email}')"

# -------------------------
# Sala/Quarto
# -------------------------
class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    capacity = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    reservations = db.relationship('Reserva', backref='room', lazy=True)

    def __repr__(self):
        return f'<Room {self.name}>'

# -------------------------
# Reserva
# -------------------------
class Reserva(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), default='reserved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Reserva {self.client_name} - Room {self.room_id}>"

# -------------------------
# Flask-Login
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))
