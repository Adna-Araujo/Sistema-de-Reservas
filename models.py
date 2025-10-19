from extensions import db, login_manager # Importa de extensions.py
from flask_login import UserMixin
from datetime import datetime

# ====================================================================
# CONFIGURAÇÃO DE LOGIN
# ====================================================================
# Função obrigatória para recarregar o usuário
@login_manager.user_loader
def load_user(user_id):
    # O user_id vem como string, precisamos converter para int
    return Usuario.query.get(int(user_id))

# ====================================================================
# DEFINIÇÃO DOS MODELOS (Banco de Dados)
# ====================================================================

# Modelo de Usuário (Herdando de UserMixin para o Flask-Login)
class Usuario(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    
    # Referência como STRING para evitar problemas de ordenação na inicialização
    reservas = db.relationship('Reserva', backref='autor', lazy=True)

    def __repr__(self):
        return f"Usuario('{self.username}', '{self.email}')"

# Modelo de Reserva (Será totalmente implementado na Fase 3)
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sala = db.Column(db.String(100), nullable=False)
    data_hora_inicio = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Chave estrangeira ligando a reserva ao usuário
    # 'usuario.id' usa o nome da tabela em minúsculo, conforme convenção do SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)

    def __repr__(self):
        return f"Reserva('{self.sala}', '{self.data_hora_inicio}')"
