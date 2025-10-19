# Importações
# ======================
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
from forms import RegistrationForm, LoginForm, ReservaForm
from models import Usuario, Reserva, Room
from extensions import db, login_manager
from sqlalchemy.exc import IntegrityError

# ======================
# Função Factory
# ======================
def create_app(config_class=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa extensões
    db.init_app(app)
    bcrypt = Bcrypt(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    # Cria tabelas
    with app.app_context():
        db.create_all()

    # ======================
    # Login Manager
    # ======================
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # ======================
    # Rotas
    # ======================
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
                flash(f'Conta criada com sucesso para {form.username.data}!', 'success')
                return redirect(url_for('login'))
            except IntegrityError:
                db.session.rollback()
                flash('Erro: Usuário ou e-mail já existe.', 'danger')
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

    # ----------------------
    # Listar Salas
    # ----------------------
    @app.route("/salas")
    @login_required
    def listar_salas():
        salas = Room.query.filter_by(is_active=True).all()
        agora = datetime.utcnow()

        salas_com_status = []
        for sala in salas:
            reserva_ativa = Reserva.query.filter(
                Reserva.room_id == sala.id,
                Reserva.start_time <= agora,
                Reserva.end_time >= agora,
                Reserva.status == 'reserved'
            ).first()

            salas_com_status.append({
                'id': sala.id,
                'name': sala.name,
                'description': sala.description,
                'capacity': sala.capacity,
                'status': "Ocupada" if reserva_ativa else "Livre"
            })

        return render_template("salas.html", salas=salas_com_status)

    # ----------------------
    # Fazer Reserva
    # ----------------------
    @app.route("/reservar", methods=['GET', 'POST'])
    @login_required
    def reservar():
        # Pega sala_id da URL para pré-selecionar no formulário
        sala_id = request.args.get("sala_id", type=int)
        form = ReservaForm(sala_id=sala_id)  # passa sala_id para o formulário

        if form.validate_on_submit():
            inicio = form.inicio.data
            duracao_horas = int(form.duracao.data)
            fim = inicio + timedelta(hours=duracao_horas)

            # Checa conflito
            conflito = Reserva.query.filter(
                Reserva.room_id == form.sala.data,
                Reserva.status == 'reserved',
                Reserva.start_time < fim,
                Reserva.end_time > inicio
            ).first()

            if conflito:
                flash("A sala já está reservada nesse horário.", "danger")
                return redirect(url_for('reservar', sala_id=form.sala.data))

            # Cria reserva
            nova_reserva = Reserva(
                room_id=form.sala.data,
                start_time=inicio,
                end_time=fim,
                client_name=current_user.username,
                status='reserved'
            )
            db.session.add(nova_reserva)
            db.session.commit()
            flash("Reserva realizada com sucesso!", "success")
            return redirect(url_for('listar_salas'))

        return render_template("reservar.html", title='Fazer Reserva', form=form)

    return app


# ======================
# Instância global
# ======================
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
