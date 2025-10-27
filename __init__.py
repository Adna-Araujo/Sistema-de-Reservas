import os
from flask import Flask, redirect, url_for, request, Response # ADICIONADAS: request, Response
from flask_bcrypt import Bcrypt
from flask_login import current_user
from flask_admin.contrib.sqla import ModelView
from datetime import timezone, datetime # ADICIONADA: datetime
from .extensions import db, login_manager, admin 
from .models import Usuario, Reserva, Room 
from flask_admin import BaseView, expose
from sqlalchemy import func
import csv # ADICIONADA: csv
from io import StringIO # ADICIONADA: StringIO

# Crie a instância global de Bcrypt
bcrypt = Bcrypt() 

# ----------------------------------------------------
# --- CLASSE MIX-IN DE SEGURANÇA ---
# ----------------------------------------------------
class SecureBaseViewMixin:
    """Mix-in que adiciona a lógica de segurança de admin a qualquer BaseView ou ModelView."""
    def is_accessible(self):
        # Apenas permite acesso se o usuário estiver autenticado E for admin
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # Redireciona para a página de login se não estiver logado
        if not current_user.is_authenticated:
            return redirect(url_for('main_bp.login'))
        # Se logado, mas não for admin
        return "Acesso Negado", 403

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
    
    # ----------------------------------------------------
    # Função auxiliar para obter dados (usada por index e export)
    # ----------------------------------------------------
    def _obter_dados_reservas(self, data_inicio_obj=None, data_fim_obj=None):
        data_coluna = Reserva.start_time
        # Cria a coluna de data formatada para agrupamento (string YYYY-MM-DD)
        data_formatada = func.strftime('%Y-%m-%d', data_coluna)
        
        query = db.session.query(
            data_formatada.label('data'),
            func.count(Reserva.id).label('total_reservas')
        ).group_by('data').order_by('data')

        # Aplica filtro de data de início
        if data_inicio_obj:
            # Compara o datetime do DB com o objeto datetime de início
            query = query.filter(data_coluna >= data_inicio_obj)
        
        # Aplica filtro de data de fim
        if data_fim_obj:
            # Compara a data string do DB com a data string final, 
            # garantindo que todo o dia final seja incluído
            data_fim_str = data_fim_obj.strftime('%Y-%m-%d')
            query = query.filter(data_formatada <= data_fim_str)
            
        return query.all()

    # ----------------------------------------------------
    # Endpoint principal (com filtros e dados para gráfico)
    # ----------------------------------------------------
    @expose('/')
    def index(self):
        # 1. Obter e processar filtros do request (strings YYYY-MM-DD)
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        data_inicio_obj = None
        data_fim_obj = None

        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
            except ValueError:
                data_inicio = None # Invalida se falhar a conversão
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            except ValueError:
                data_fim = None # Invalida se falhar a conversão

        # 2. Obter dados filtrados
        relatorio = self._obter_dados_reservas(data_inicio_obj, data_fim_obj)
        
        # 3. Preparar dados para o gráfico (JSON)
        labels = [item.data for item in relatorio]
        data_values = [item.total_reservas for item in relatorio]
        
        # 4. Renderiza o template
        return self.render(
            'relatorio_reservas.html', 
            relatorio=relatorio,
            labels=labels,        # Para o gráfico
            data_values=data_values, # Para o gráfico
            data_inicio=data_inicio, # Valor atual do filtro (para o formulário)
            data_fim=data_fim,       # Valor atual do filtro (para o formulário)
            name="Relatório de Reservas Diárias"
        )
        
    # ----------------------------------------------------
    # Novo Endpoint para Exportação CSV
    # ----------------------------------------------------
    @expose('/export/')
    def export_csv(self):
        # Reutiliza a lógica de filtro
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        data_inicio_obj = None
        data_fim_obj = None
        
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
            except ValueError:
                pass

        dados = self._obter_dados_reservas(data_inicio_obj, data_fim_obj)

        # 1. Cria um buffer de string na memória
        si = StringIO()
        cw = csv.writer(si)

        # 2. Escreve o cabeçalho
        cw.writerow(['Data', 'Total de Reservas'])

        # 3. Escreve os dados
        # O SQLAlchemy retorna objetos Row, então convertemos para listas de valores
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
    
    # Configurações do App
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key_if_not_set')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ----------------------
    # Inicialização das Extensões
    # ----------------------
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    admin.init_app(app)
    login_manager.login_view = 'main_bp.login'
    login_manager.login_message_category = 'info'
    
    # ----------------------
    # Configuração das Views do Flask-Admin
    # ----------------------
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
    # Criação das Tabelas
    # ----------------------
    with app.app_context():
        db.create_all()

    return app
