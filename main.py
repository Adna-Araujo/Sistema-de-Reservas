# Importações de módulos
import os
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, ReservaForm
from models import Usuario, Reserva, Room
from extensions import db, login_manager  # Importa as extensões globais
from sqlalchemy.exc import IntegrityError  # Importa para lidar com erros de BD


# ==============================
# Função Factory para criar app
# ==============================
def create_app(config_class=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa as extensões com o app
    db.init_app(app)
    bcrypt = Bcrypt(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    # Cria tabelas do banco
    with app.app_context():
        db.create_all()

    # =======================
    # Funções e Rotas Flask
    # =======================
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    @app.route("/")
    @app.route("/index")
    def index():
        return render_template('index.html', status="Estrutura de Templates OK!")

    @app.route("/register", methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegistrationForm()
        if form.validate_on_submit():
            try:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                user = Usuario(username=form.username.data, email=form.email.data, password=hashed_password)
                db.session.add(user)
                db.session.commit()
                flash(f'Conta criada com sucesso para {form.username.data}! Agora você pode fazer o login.', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('Erro ao criar conta. Usuário ou e-mail já existe.', 'danger')
            except Exception as e:
                db.session.rollback()
                flash(f'Ocorreu um erro inesperado: {e}', 'danger')
        
        return render_template('register.html', title='Cadastro', form=form)

    @app.route("/login", methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = db.session.execute(db.select(Usuario).filter_by(email=form.email.data)).scalar_one_or_none()

            if user and bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                flash('Login realizado com sucesso!', 'success')
                return redirect(next_page or url_for('index'))
            else:
                flash('Falha no login. Verifique o e-mail e a senha.', 'danger')
        
        return render_template('login.html', title='Login', form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash('Você saiu da sua conta.', 'info')
        return redirect(url_for('index'))

    @app.route("/reservar", methods=['GET', 'POST'])
    @login_required
    def reservar():
        form = ReservaForm()
        # A lógica de reserva virá depois
        return render_template('reservar.html', title='Fazer Reserva', form=form)

    return app


# ====================================================
# 🔹 Adicionado: Instancia app globalmente p/ seed.py
# ====================================================
app = create_app()

# ====================================================
# Inicialização direta (modo desenvolvimento)
# ====================================================
if __name__ == '__main__':
    app.run(debug=True)
