# Importações
# ======================
import os
from datetime import datetime, timedelta, timezone 
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_bcrypt import Bcrypt
from flask_login import current_user, login_user, logout_user, login_required
# Garantindo que o RoomForm seja importado, embora eu o importe localmente nas rotas que o usam
from forms import RegistrationForm, LoginForm, ReservaForm, RoomForm 
from models import Usuario, Reserva, Room
from extensions import db, login_manager
from sqlalchemy.exc import IntegrityError
from functools import wraps

# ----------------------
# Decorator de Restrição de Admin
# ----------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Checa se o usuário está autenticado
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'info')
            return redirect(url_for('login')) 
            
        # 2. Checa se o usuário é administrador
        if not current_user.is_admin:
            flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
            return redirect(url_for('index'))
            
        # Se for admin, executa a função da rota
        return f(*args, **kwargs)
    return decorated_function

# ======================
# Função Factory
# ======================
def create_app(config_class=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # ----------------------
    # Variáveis Globais para o Template (Context Processor)
    # ----------------------
  

    # Inicializa extensões
    db.init_app(app)
    bcrypt = Bcrypt(app)
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'

    # ----------------------
    # Filtro Jinja para corrigir fuso horário
    # ----------------------
    @app.template_filter('ensure_utc')
    def ensure_utc_filter(dt):
        """Força o datetime para UTC se for offset-naive (sem fuso horário)."""
        from datetime import timezone
        if dt and dt.tzinfo is None:
            # Assumimos que dados sem tzinfo foram salvos como UTC
            return dt.replace(tzinfo=timezone.utc)
        return dt
    
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
    # Dashboard de Administração
    # ----------------------
    @app.route("/admin/dashboard")
    @login_required
    @admin_required
    def dashboard():
        todas_reservas = Reserva.query.order_by(
            Reserva.start_time.asc()
        ).all()
        
        todas_salas = Room.query.all()

        return render_template(
            'dashboard.html', 
            title='Painel de Administração',
            reservas=todas_reservas,
            salas=todas_salas
        )
    
    # ----------------------
    # Gerenciar Salas (CRUD Read/List)
    # ----------------------
    @app.route("/admin/salas")
    @login_required
    @admin_required
    def gerenciar_salas():
        salas = Room.query.order_by(Room.name.asc()).all()
        
        return render_template(
            'gerenciar_salas.html', 
            title='Gerenciar Salas', 
            salas=salas
        )
    
    # ----------------------
    # Adicionar Sala (CRUD Create)
    # ----------------------
    @app.route("/admin/sala/adicionar", methods=['GET', 'POST'])
    @login_required
    @admin_required
    def adicionar_sala():
        from forms import RoomForm 
        form = RoomForm()
        
        form.room_id = None 

        if form.validate_on_submit():
            nova_sala = Room(
                name=form.name.data,
                description=form.description.data,
                capacity=form.capacity.data,
                is_active=form.is_active.data
            )
            db.session.add(nova_sala)
            db.session.commit()
            flash(f"Sala '{nova_sala.name}' adicionada com sucesso!", 'success')
            return redirect(url_for('gerenciar_salas'))

        return render_template(
            'sala_form.html', 
            title='Adicionar Nova Sala', 
            form=form
        )

    # ----------------------
    # Editar Sala (CRUD Update)
    # ----------------------
    @app.route("/admin/sala/<int:sala_id>/editar", methods=['GET', 'POST'])
    @login_required
    @admin_required
    def editar_sala(sala_id):
        from forms import RoomForm 
        sala = db.session.get(Room, sala_id)

        if not sala:
            flash("Sala não encontrada.", "danger")
            return redirect(url_for('gerenciar_salas'))

        form = RoomForm(obj=sala)
        
        form.room_id = sala.id 

        if form.validate_on_submit():
            sala.name = form.name.data
            sala.description = form.description.data
            sala.capacity = form.capacity.data
            sala.is_active = form.is_active.data
            
            db.session.commit()
            flash(f"Sala '{sala.name}' atualizada com sucesso!", 'success')
            return redirect(url_for('gerenciar_salas'))
        
        return render_template(
            'sala_form.html', 
            title=f'Editar Sala: {sala.name}', 
            form=form
        )
        
    # ----------------------
    # Cancelar Reserva (ADMIN)
    # ----------------------
    @app.route("/admin/reserva/<int:reserva_id>/cancelar", methods=['POST'])
    @login_required
    @admin_required
    def admin_cancelar_reserva(reserva_id):
        reserva = db.session.get(Reserva, reserva_id)
        
        if not reserva:
            flash("Reserva não encontrada.", "danger")
            return redirect(url_for('dashboard'))

        if reserva.status != 'reserved':
            flash(f"Reserva #{reserva.id} já foi cancelada ou concluída.", "danger")
            return redirect(url_for('dashboard'))

        reserva.status = 'cancelled'
        reserva.cancelled_at = datetime.now(timezone.utc)
        
        db.session.commit()
        username = reserva.reserver.username if reserva.reserver else "Usuário Desconhecido"
        flash(f"Reserva #{reserva.id} de {username} cancelada pelo Admin.", "success")
        
        return redirect(url_for('dashboard'))
    # ----------------------
    # Fim das rotas administrativas
    # ----------------------
    
    # ----------------------
    # Listar Salas
    # ----------------------
    @app.route("/salas")
    @login_required
    def listar_salas():
        salas = Room.query.filter_by(is_active=True).all()
        # O 'agora' aqui é offset-aware, necessário para a lógica de 'ocupada'
        agora = datetime.now(timezone.utc) 

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
        sala_id_arg = request.args.get("sala_id", type=int)
        form = ReservaForm() 

        # 1. Popular o SelectField 'sala' com dados do banco
        salas = Room.query.filter_by(is_active=True).all()
        form.sala.choices = [(s.id, s.name) for s in salas]
        
        sala_selecionada = None

        # Pré-selecionar a sala
        if sala_id_arg and sala_id_arg in [s.id for s in salas]:
            form.sala.data = sala_id_arg
            sala_selecionada = db.session.get(Room, sala_id_arg) 

        if form.validate_on_submit():
            inicio = form.inicio.data
            
            # Aplica o fuso horário UTC (CORREÇÃO DO TYPERROR)
            if inicio.tzinfo is None:
                inicio = inicio.replace(tzinfo=timezone.utc)

            duracao_horas = int(form.duracao.data)
            fim = inicio + timedelta(hours=duracao_horas)
            room_id = form.sala.data
        
            # Validação: garantir que a data de início não seja no passado
            if inicio < datetime.now(timezone.utc): 
                flash("A data e hora de início não podem ser no passado.", "danger")
            
            else: # Se a data for válida, prossegue com a checagem de conflito
                # Checa conflito
                conflito = Reserva.query.filter(
                    Reserva.room_id == room_id,
                    Reserva.status == 'reserved',
                    Reserva.start_time < fim,
                    Reserva.end_time > inicio
                ).first()

                if conflito:
                    flash("A sala já está reservada nesse horário.", "danger")
                    return redirect(url_for('reservar', sala_id=room_id))

                # Cria reserva
                nova_reserva = Reserva(
                    room_id=room_id,
                    user_id=current_user.id, 
                    start_time=inicio,
                    end_time=fim,
                    client_name=current_user.username,
                    status='reserved'
                )
                db.session.add(nova_reserva)
                db.session.commit()
                flash("Reserva realizada com sucesso!", "success")
                return redirect(url_for('minhas_reservas')) 

        sala_disabled = True if sala_selecionada else False

        return render_template(
            "reservar.html", 
            title='Fazer Reserva', 
            form=form,
            sala_disabled=sala_disabled,
            sala_nome=sala_selecionada.name if sala_selecionada else None
        )
    
    # ----------------------
    # Minhas Reservas (CORRIGIDA)
    # ----------------------
    @app.route("/minhas_reservas")
    @login_required
    def minhas_reservas():
    # Calcular o tempo atual, garantindo que é offset-aware (UTC)
        agora_utc = datetime.now(timezone.utc) 
        reservas = Reserva.query.filter_by(
            user_id=current_user.id
        ).order_by(
            Reserva.start_time.asc()
        ).all()
    # O TEMPO ATUAL É PASSADO PARA O TEMPLATE COMO 'agora'
        return render_template(
            'minhas_reservas.html', 
            title='Minhas Reservas', 
            reservas=reservas,
            agora=agora_utc # VARIÁVEL UTC CORRIGIDA E ENVIADA
        )
    
    # ----------------------
    # Cancelar Reserva (Usuário)
    # ----------------------
    @app.route("/reserva/<int:reserva_id>/cancelar", methods=['POST'])
    @login_required
    def cancelar_reserva(reserva_id):
        reserva = db.session.get(Reserva, reserva_id)
        
        if not reserva:
            flash("Reserva não encontrada.", "danger")
            return redirect(url_for('minhas_reservas'))

        if reserva.user_id != current_user.id:
            flash("Você não tem permissão para cancelar esta reserva.", "danger")
            return redirect(url_for('minhas_reservas'))

        if reserva.status != 'reserved':
            flash("Esta reserva já foi cancelada ou concluída.", "danger")
            return redirect(url_for('minhas_reservas'))

        reserva.status = 'cancelled'
        reserva.cancelled_at = datetime.now(timezone.utc)
        
        db.session.commit()
        flash(f"Reserva #{reserva.id} cancelada com sucesso!", "success")
        
        return redirect(url_for('minhas_reservas'))
        
    return app


# ======================
# Instância global
# ======================
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)