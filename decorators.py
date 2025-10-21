# C:\projetos\sistema de reservas\reservas\decorators.py

from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def admin_required(f):
    """
    Verifica se o usuário logado é um administrador. 
    Redireciona para a página de 'Minhas Reservas' se o acesso for negado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. Checa se o usuário está autenticado
        if not current_user.is_authenticated:
            flash('Você precisa fazer login para acessar esta página.', 'info')
            return redirect(url_for('main_bp.login')) 
            
        # 2. Checa se o usuário é administrador (Assumindo campo 'is_admin' no modelo Usuario)
        if not current_user.is_admin:
            flash('Acesso negado. Você não tem permissão de administrador.', 'danger')
            # Redireciona para a rota 'minhas_reservas' (que está no Blueprint 'main_bp')
            return redirect(url_for('main_bp.minhas_reservas')) 
            
        return f(*args, **kwargs)
    return decorated_function