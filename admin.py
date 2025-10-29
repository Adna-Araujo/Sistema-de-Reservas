from flask_admin import AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, request, flash

# =================================================================
# CLASSE BASE DE SEGURANÇA (MIDDLEWARE/DECORADOR)
# =================================================================
class ProtectedAdminView:
    """
    Classe Mixin que implementa a verificação de login e permissão de admin
    para todas as views do Flask-Admin que a herdarem.
    """
    def is_accessible(self):
        # 1. O usuário deve estar logado E
        # 2. O usuário logado deve ter o atributo 'is_admin' como True
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        # Se o usuário NÃO estiver logado, redireciona para a página de login
        if not current_user.is_authenticated:
            # Assumindo que sua rota de login está no blueprint 'main_bp'
            return redirect(url_for('main_bp.login', next=request.url))
            
        # Se estiver logado, mas NÃO for admin (Acesso Negado 403)
        # É uma prática comum no Flask-Admin retornar um 403 aqui.
        return '<h1>Acesso Negado: Você não é administrador</h1>', 403
        
# =================================================================
# 1. VIEW DO DASHBOARD PRINCIPAL (INDEX)
# =================================================================
class MyAdminIndexView(ProtectedAdminView, AdminIndexView):
    pass # Herda a proteção

# =================================================================
# 2. VIEWS DOS MODELOS (Todas herdam a proteção)
# =================================================================
class RoomAdminView(ProtectedAdminView, ModelView):
    # Exemplo: Adicione configurações específicas do modelo Room aqui
    # form_columns = ['name', 'description', 'price']
    pass

class UsuarioAdminView(ProtectedAdminView, ModelView):
    # Recomendação: Oculte o hash da senha
    column_exclude_list = ['password_hash']
    form_excluded_columns = ['password_hash']
    pass

class ReservaAdminView(ProtectedAdminView, ModelView):
    # Exemplo: Defina colunas visíveis ou filtros
    # column_list = ['room', 'user', 'start_date', 'end_date']
    pass

# =================================================================
# 3. VIEW PERSONALIZADA DE RELATÓRIO
# =================================================================
class RelatorioReservasView(ProtectedAdminView, BaseView):
    @expose('/')
    def index(self):
        # Lógica para obter dados do relatório aqui
        return self.render('admin/relatorio_reservas.html')

# Repita esta herança para todas as views de modelo: Usuario, Reserva, RelatorioView, etc.