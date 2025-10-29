import os
from flask import Flask, redirect, url_for, request, Response
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from datetime import timezone, datetime
from .extensions import db, login_manager, admin, bcrypt 
from .models import Usuario, Reserva, Room 
from flask_admin import BaseView, expose, AdminIndexView 
from sqlalchemy import func
import csv
from io import StringIO
from .cli import init_cli

# ----------------------------------------------------
# --- CLASSE MIX-IN DE SEGURANÇA (AUTORIZAÇÃO) ---
# ----------------------------------------------------
class SecureBaseViewMixin:
# ... (conteúdo da classe omitido por brevidade, está OK)
    def is_accessible(self):
        # Apenas permite acesso se o usuário estiver autenticado E for admin
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # Redireciona para a página de login, passando a URL atual como 'next'
        if not current_user.is_authenticated:
            # Assumindo que a rota de login é 'main_bp.login'
            return redirect(url_for('main_bp.login', next=request.url))
        # Se logado, mas não for admin, nega o acesso
        return "Acesso Negado", 403

# ----------------------------------------------------
# --- CLASSE PARA PROTEÇÃO DA PÁGINA INICIAL DO ADMIN ---
# ----------------------------------------------------
class MyAdminIndexView(SecureBaseViewMixin, AdminIndexView):
    # Esta classe garante que /admin/ só carregue para admins
    pass

# ----------------------------------------------------
# --- CLASSES DE VIEWS PARA MODELOS (CRUD) ---
# ----------------------------------------------------
class BaseAdminView(SecureBaseViewMixin, ModelView):
    pass

class RoomAdminView(BaseAdminView):
    pass

class ReservaAdminView(BaseAdminView):
    pass

class UsuarioAdminView(BaseAdminView):
    # Proteção de senha: não exibe na lista nem nos formulários
    column_exclude_list = ('password',)
    form_excluded_columns = ('password',)

# ----------------------------------------------------
# --- CLASSE DE VIEW CUSTOMIZADA (RELATÓRIO) ---
# ----------------------------------------------------
class RelatorioReservasView(SecureBaseViewMixin, BaseView):
# ... (todo o código do relatório, que está OK)
    def _obter_dados_reservas(self, data_inicio_obj=None, data_fim_obj=None):
        data_coluna = Reserva.start_time
        data_agrupada = func.date(data_coluna).label('data')
        
        query = db.session.query(
            data_agrupada,
            func.count(Reserva.id).label('total_reservas')
        ).group_by(data_agrupada).order_by(data_agrupada)

        # Aplica filtro de data de início
        if data_inicio_obj:
            query = query.filter(data_coluna >= data_inicio_obj)
        
        # Aplica filtro de data de fim (adiciona 23:59:59 para incluir o dia inteiro)
        if data_fim_obj:
            data_fim_inclusiva = data_fim_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(data_coluna <= data_fim_inclusiva)
            
        return query.all()

    @expose('/')
    def index(self):
        # 1. Obter e processar filtros do request (strings YYYY-MM-DD)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        data_inicio_obj = None
        data_fim_obj = None

        if data_inicio:
            try:
                # O filtro do relatório funciona melhor com objetos datetime
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                data_inicio = None 
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                data_fim = None

        # 2. Obter dados filtrados
        relatorio = self._obter_dados_reservas(data_inicio_obj, data_fim_obj)
        
        # 3. Preparar dados para o gráfico (JSON)
        labels = [item.data for item in relatorio]
        data_values = [item.total_reservas for item in relatorio]
        
        # 4. Renderiza o template
        return self.render(
            'admin/relatorio_reservas.html', 
            relatorio=relatorio,
            labels=labels, 
            data_values=data_values, 
            data_inicio=data_inicio,
            data_fim=data_fim,
            name="Relatório de Reservas Diárias"
            )
        
    @expose('/export/')
    def export_csv(self):
        # Lógica de filtro idêntica à de index
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        data_inicio_obj = None
        data_fim_obj = None
        
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            except ValueError:
                pass

        dados = self._obter_dados_reservas(data_inicio_obj, data_fim_obj)

        # 1. Cria um buffer de string na memória
        si = StringIO()
        cw = csv.writer(si)

        # 2. Escreve o cabeçalho
        cw.writerow(['Data', 'Total de Reservas'])

        # 3. Escreve os dados
        cw.writerows([(item.data, item.total_reservas) for item in dados])

        # 4. Retorna a resposta HTTP
        output = si.getvalue()
        
        return Response(
            output,
            mimetype='text/csv',
            headers={
                "Content-Disposition": "attachment;filename=relatorio_reservas.csv",
                "Cache-Control": "no-cache"
            }
        )

def create_app(config_class=None):
    # ----------------------
    # Configuração da Aplicação
    # ----------------------
    app = Flask('reservas') 
    
    # ----------------------------------------------------
    # 1. DEFINIÇÃO DAS CONFIGURAÇÕES DO APP (CORREÇÃO DE ORDEM)
    # ----------------------------------------------------
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ADMIN_SWATCH'] = 'darkly' 
    
    # ----------------------
    # 2. Inicialização das Extensões
    # ----------------------
    db.init_app(app) 
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    admin.init_app(app) 
    
    # Configurações Adicionais do Admin
    admin.name = 'Painel Administrativo' # Nome mais descritivo
    admin.base_template = 'admin/master.html'
    admin.template_mode = 'bootstrap4'
    
    login_manager.login_view = 'main_bp.login'
    login_manager.login_message_category = 'info'
    
    # ----------------------
    # Configuração das Views do Flask-Admin
    # ----------------------
    admin.add_view(MyAdminIndexView(name='Dashboard', url='/admin', endpoint='admin_dashboard'))
    
    admin.add_view(RoomAdminView(Room, db.session, name='Salas (Rooms)'))
    admin.add_view(ReservaAdminView(Reserva, db.session, name='Reservas'))
    admin.add_view(UsuarioAdminView(Usuario, db.session, name='Usuários'))
    admin.add_view(RelatorioReservasView(name='Relatório Diário', endpoint='relatorio'))
    
    # ----------------------
    # Login Manager e User Loader
    # ----------------------
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))
    
    # ----------------------
    # Filtro Jinja para corrigir fuso horário
    # ----------------------
    @app.template_filter('ensure_utc')
    def ensure_utc_filter(dt):
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    # ----------------------
    # Registro dos Blueprints (Rotas)
    # ----------------------
    from .routes import main_bp
    app.register_blueprint(main_bp)
    
    # ----------------------
    # Registro dos Comandos CLI (NOVO)
    # ----------------------
    init_cli(app)

    # ----------------------
    # Criação das Tabelas
    # ----------------------
    with app.app_context():
        db.create_all()

    return app