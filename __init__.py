# C:\projetos\sistema de reservas\reservas\__init__.py

import os
from flask import Flask
from flask_bcrypt import Bcrypt
from .extensions import db, login_manager # Importações relativas
from .models import Usuario

# Crie a instância global de Bcrypt aqui, pois ela é inicializada no create_app
bcrypt = Bcrypt() 

def create_app(config_class=None):
    # ----------------------
    # Configuração da Aplicação
    # ----------------------
    # __name__ indica o pacote 'reservas'
    app = Flask('reservas') 
    
    # Configurações do App
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ----------------------
    # Inicialização das Extensões
    # ----------------------
    db.init_app(app)
    bcrypt.init_app(app) # Inicializa Bcrypt
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    
    # ----------------------
    # Login Manager e User Loader
    # ----------------------
    # A importação do modelo é feita dentro da função para evitar problemas circulares
    from .models import Usuario 

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))
    
    # ----------------------
    # Filtro Jinja para corrigir fuso horário
    # ----------------------
    from datetime import timezone
    @app.template_filter('ensure_utc')
    def ensure_utc_filter(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    # ----------------------
    # Registro dos Blueprints (Rotas)
    # ----------------------
    # 1. Rotas Comuns
    from .routes import main_bp
    app.register_blueprint(main_bp)

    # 2. Rotas Administrativas
    from .admin.routes import admin_bp 
    app.register_blueprint(admin_bp)

    # ----------------------
    # Criação das Tabelas
    # ----------------------
    with app.app_context():
        db.create_all()

    return app