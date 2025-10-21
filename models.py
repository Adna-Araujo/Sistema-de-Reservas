from .extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime, timezone # <-- ADICIONADA A IMPORTAÇÃO DE TIMEZONE

# -------------------------
# Função para default de data/hora (Timezone-aware)
# -------------------------
def get_utc_now():
    """Retorna o datetime.now(timezone.utc) para evitar warnings e garantir consistência."""
    return datetime.now(timezone.utc)

# -------------------------
# Usuário
# -------------------------
class Usuario(db.Model, UserMixin):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    #ADIÇÃO PARA CONTROLE DE ADMINISTRAÇÃO
    is_admin = db.Column(db.Boolean, default=False)

    reservas = db.relationship('Reserva', backref='autor', lazy=True)

    def __repr__(self):
        return f"Usuario('{self.username}', '{self.email}', Admin: {self.is_admin})"

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
    
    # ⚠️ MUDANÇA: Usando get_utc_now como default (corrigindo o Warning)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(20), default='reserved')
    # ⚠️ MUDANÇA: Usando get_utc_now como default
    created_at = db.Column(db.DateTime, default=get_utc_now)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<Reserva {self.client_name} - Room {self.room_id}>"

# -------------------------
# Flask-Login
# -------------------------
@login_manager.user_loader
def load_user(user_id):
    # ⚠️ MUDANÇA: Usando db.session.get (correção do LegacyAPIWarning)
    return db.session.get(Usuario, int(user_id))