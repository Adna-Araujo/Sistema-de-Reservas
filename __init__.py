import os
import csv
from io import StringIO
from flask import Flask, redirect, url_for, request, Response
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from datetime import timezone, datetime
from .extensions import db, login_manager, admin, bcrypt 
from .models import Usuario, Reserva, Room 
from flask_admin import BaseView, expose, AdminIndexView 
from sqlalchemy import func
from .cli import init_cli

# --- CLASSE MIX-IN DE SEGURANÇA ---
class SecureBaseViewMixin:
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('main_bp.login', next=request.url))
        return "Acesso Negado", 403

# --- CLASSE PARA O DASHBOARD CUSTOMIZADO ---
class MyAdminIndexView(SecureBaseViewMixin, AdminIndexView):
    @expose('/')
    def index(self):
        total_reservas = Reserva.query.count()
        total_rooms = Room.query.count()
        ultimas = Reserva.query.order_by(Reserva.id.desc()).limit(5).all()
        
        return self.render('admin/dashboard.html', 
                           total_reservas=total_reservas,
                           total_rooms=total_rooms,
                           ultimas_reservas=ultimas)

# --- CLASSES DE VIEWS PARA MODELOS ---
class BaseAdminView(SecureBaseViewMixin, ModelView):
    pass

class RoomAdminView(BaseAdminView):
    pass

class ReservaAdminView(BaseAdminView):
    pass

class UsuarioAdminView(BaseAdminView):
    column_exclude_list = ('password',)
    form_excluded_columns = ('password',)

# --- CLASSE DE RELATÓRIO ---
class RelatorioReservasView(SecureBaseViewMixin, BaseView):
    def _obter_dados_reservas(self, data_inicio_obj=None, data_fim_obj=None):
        data_coluna = Reserva.start_time
        data_agrupada = func.date(data_coluna).label('data')
        query = db.session.query(data_agrupada, func.count(Reserva.id).label('total_reservas')).group_by(data_agrupada).order_by(data_agrupada)
        if data_inicio_obj: query = query.filter(data_coluna >= data_inicio_obj)
        if data_fim_obj: query = query.filter(data_coluna <= data_fim_obj.replace(hour=23, minute=59, second=59))
        return query.all()

    @expose('/')
    def index(self):
        relatorio = self._obter_dados_reservas()
        labels = [str(item.data) for item in relatorio]
        data_values = [item.total_reservas for item in relatorio]
        return self.render('admin/relatorio_reservas.html', 
                           relatorio=relatorio, 
                           labels=labels, 
                           data_values=data_values, 
                           name="Relatório Diário")

    @expose('/export/')
    def export_csv(self):
        relatorio = self._obter_dados_reservas()
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Data', 'Total de Reservas'])
        cw.writerows([(item.data, item.total_reservas) for item in relatorio])
        
        return Response(
            si.getvalue(),
            mimetype='text/csv',
            headers={"Content-Disposition": "attachment;filename=relatorio_reservas.csv"}
        )

def create_app(config_class=None):
    app = Flask('reservas') 
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly' 
    
    db.init_app(app) 
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # --- LÓGICA DE PROTEÇÃO DO ADMIN ---
    if admin.app is not None:
        admin.app = None
        admin.blueprint = None

    admin.init_app(app, index_view=MyAdminIndexView(name='Home', url='/admin', template='admin/dashboard.html'))
    
    admin.name = 'EscapingRooms Admin'
    admin.template_mode = 'bootstrap4'
    admin._views = [] 

    admin.add_view(RoomAdminView(Room, db.session, name='Salas', endpoint='view_salas_final'))
    admin.add_view(ReservaAdminView(Reserva, db.session, name='Reservas', endpoint='view_reservas_final'))
    admin.add_view(UsuarioAdminView(Usuario, db.session, name='Usuários', endpoint='view_usuarios_final'))
    admin.add_view(RelatorioReservasView(name='Relatório Diário', endpoint='view_relatorio_final'))

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))
    
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    init_cli(app)

    with app.app_context():
        db.create_all()

    return app