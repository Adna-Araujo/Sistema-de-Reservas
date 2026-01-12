# C:\projetos\sistema de reservas\reservas\routes.py

from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta, timezone

# Importações Locais
from .forms import RegistrationForm, LoginForm, ReservaForm 
from .models import Usuario, Reserva, Room
from . import bcrypt # Importa o bcrypt que está no __init__
from .extensions import db # Importa o db que está no extensions


# Define o Blueprint para as rotas principais
main_bp = Blueprint('main_bp', __name__) 


# ======================
# Rotas Comuns
# ======================

@main_bp.route("/")
@main_bp.route("/index")
def index():
    return render_template('home_usuario.html', status="Estrutura de Templates OK!")

@main_bp.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('.index')) # Note o .index para rotas do mesmo Blueprint

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Note o uso do bcrypt importado
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            # ❗ CORREÇÃO: Você está usando 'username' no código, mas o modelo deve ser 'nome' ou 'username'. 
            # Assumindo que seu modelo Usuario tem 'username' e 'password'.
            user = Usuario(username=form.username.data, email=form.email.data, password=hashed_password) 
            db.session.add(user)
            db.session.commit()
            flash(f'Conta criada com sucesso para {form.username.data}!', 'success')
            return redirect(url_for('.login'))
        except IntegrityError:
            db.session.rollback()
            flash('Erro: Usuário ou e-mail já existe.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado: {e}', 'danger')

    return render_template('register.html', title='Cadastro', form=form)

@main_bp.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.execute(db.select(Usuario).filter_by(email=form.email.data)).scalar_one_or_none()
        
        # CORREÇÃO: Converte o hash salvo no banco (user.password) de string para bytes
        # O Flask-Bcrypt (por baixo dos panos) espera o hash salvo como bytes para evitar o 'Invalid salt'
        user_password_bytes = user.password.encode('utf-8') if user and user.password else b''
        
        # AQUI estava o problema: 
        if user and user_password_bytes and bcrypt.check_password_hash(user_password_bytes, form.password.data):
        
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page or url_for('.index'))
        else:
            flash('Falha no login. Verifique o e-mail e a senha.', 'danger')

    return render_template('login.html', title='Login', form=form)

@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('.index'))

# ----------------------
# Listar Salas
# ----------------------
@main_bp.route("/salas")
@login_required
def listar_salas():
    salas = Room.query.filter_by(is_active=True).all()
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
@main_bp.route("/reservar", methods=['GET', 'POST'])
@login_required
def reservar():
    sala_id_arg = request.args.get("sala_id", type=int)
    form = ReservaForm() 

    # 1. Popular o SelectField 'sala'
    salas = Room.query.filter_by(is_active=True).all()
    form.sala.choices = [(s.id, s.name) for s in salas]
    
    sala_selecionada = None

    # Pré-selecionar a sala
    if sala_id_arg and sala_id_arg in [s.id for s in salas]:
        form.sala.data = sala_id_arg
        sala_selecionada = db.session.get(Room, sala_id_arg) 

    if form.validate_on_submit():
        inicio = form.inicio.data
        
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)

        duracao_horas = int(form.duracao.data)
        fim = inicio + timedelta(hours=duracao_horas)
        room_id = form.sala.data
    
        # Validação: data de início não pode ser no passado
        if inicio < datetime.now(timezone.utc): 
            flash("A data e hora de início não podem ser no passado.", "danger")
        
        else: 
            # Checa conflito
            conflito = Reserva.query.filter(
                Reserva.room_id == room_id,
                Reserva.status == 'reserved',
                Reserva.start_time < fim,
                Reserva.end_time > inicio
            ).first()

            if conflito:
                flash("A sala já está reservada nesse horário.", "danger")
                return redirect(url_for('.reservar', sala_id=room_id))

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
            return redirect(url_for('.minhas_reservas')) 

    sala_disabled = True if sala_selecionada else False

    return render_template(
        "reservar.html", 
        title='Fazer Reserva', 
        form=form,
        sala_disabled=sala_disabled,
        sala_nome=sala_selecionada.name if sala_selecionada else None
    )

# ----------------------
# Minhas Reservas
# ----------------------
@main_bp.route("/minhas_reservas")
@login_required
def minhas_reservas():
    agora_utc = datetime.now(timezone.utc) 
    reservas = Reserva.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Reserva.start_time.asc()
    ).all()
    
    return render_template(
        'minhas_reservas.html', 
        title='Minhas Reservas', 
        reservas=reservas,
        agora=agora_utc
    )

# ----------------------
# Cancelar Reserva (Usuário)
# ----------------------
@main_bp.route("/reserva/<int:reserva_id>/cancelar", methods=['POST'])
@login_required
def cancelar_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for('.minhas_reservas'))

    if reserva.user_id != current_user.id:
        flash("Você não tem permissão para cancelar esta reserva.", "danger")
        return redirect(url_for('.minhas_reservas'))

    if reserva.status != 'reserved':
        flash("Esta reserva já foi cancelada ou concluída.", "danger")
        return redirect(url_for('.minhas_reservas'))

    reserva.status = 'cancelled'
    reserva.cancelled_at = datetime.now(timezone.utc)
    
    db.session.commit()
    flash(f"Reserva #{reserva.id} cancelada com sucesso!", "success")
    
    return redirect(url_for('.minhas_reservas'))