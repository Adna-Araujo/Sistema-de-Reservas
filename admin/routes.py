# C:\projetos\sistema de reservas\reservas\admin\routes.py

from flask import Blueprint, render_template, url_for, flash, redirect, request
from flask_login import login_required
from datetime import datetime, timezone

# Importações Locais
from ..decorators import admin_required 
from ..models import Reserva, Room, Usuario
from ..extensions import db
from ..forms import RoomForm # Importa RoomForm do nível superior


# Define o Blueprint para as rotas de ADMIN
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin') 


# ----------------------
# Dashboard de Administração
# ----------------------
@admin_bp.route("/dashboard")
@login_required
@admin_required # ⬅️ Aqui está o decorador de segurança
def dashboard():
    todas_reservas = Reserva.query.order_by(
        Reserva.start_time.asc()
    ).all()
    
    todas_salas = Room.query.all()

    return render_template(
        'dashboard.html', # ❗ Se você tiver um layout de template específico para admin, use 'admin/dashboard.html'
        title='Painel de Administração',
        reservas=todas_reservas,
        salas=todas_salas
    )

# ----------------------
# Gerenciar Salas (CRUD Read/List)
# ----------------------
@admin_bp.route("/salas")
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
@admin_bp.route("/sala/adicionar", methods=['GET', 'POST'])
@login_required
@admin_required
def adicionar_sala():
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
        # Redireciona para o mesmo Blueprint: .gerenciar_salas
        return redirect(url_for('.gerenciar_salas')) 

    return render_template(
        'sala_form.html', 
        title='Adicionar Nova Sala', 
        form=form
    )

# ----------------------
# Editar Sala (CRUD Update)
# ----------------------
@admin_bp.route("/sala/<int:sala_id>/editar", methods=['GET', 'POST'])
@login_required
@admin_required
def editar_sala(sala_id):
    sala = db.session.get(Room, sala_id)

    if not sala:
        flash("Sala não encontrada.", "danger")
        return redirect(url_for('.gerenciar_salas'))

    form = RoomForm(obj=sala)
    form.room_id = sala.id 

    if form.validate_on_submit():
        sala.name = form.name.data
        sala.description = form.description.data
        sala.capacity = form.capacity.data
        sala.is_active = form.is_active.data
        
        db.session.commit()
        flash(f"Sala '{sala.name}' atualizada com sucesso!", 'success')
        return redirect(url_for('.gerenciar_salas'))
    
    return render_template(
        'sala_form.html', 
        title=f'Editar Sala: {sala.name}', 
        form=form
    )
    
# ----------------------
# Cancelar Reserva (ADMIN)
# ----------------------
@admin_bp.route("/reserva/<int:reserva_id>/cancelar", methods=['POST'])
@login_required
@admin_required
def admin_cancelar_reserva(reserva_id):
    reserva = db.session.get(Reserva, reserva_id)
    
    if not reserva:
        flash("Reserva não encontrada.", "danger")
        return redirect(url_for('.dashboard'))

    if reserva.status != 'reserved':
        flash(f"Reserva #{reserva.id} já foi cancelada ou concluída.", "danger")
        return redirect(url_for('.dashboard'))

    reserva.status = 'cancelled'
    reserva.cancelled_at = datetime.now(timezone.utc)
    
    db.session.commit()
    username = reserva.reserver.username if reserva.reserver else "Usuário Desconhecido"
    flash(f"Reserva #{reserva.id} de {username} cancelada pelo Admin.", "success")
    
    return redirect(url_for('.dashboard'))