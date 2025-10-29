from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_admin import Admin

# ====================================================================
# INSTÂNCIAS GLOBAIS
# Estas são definidas aqui para serem importadas por models.py e app.py,
# evitando a importação circular.
# ====================================================================

db = SQLAlchemy()
login_manager = LoginManager()
admin = Admin(name='Painel Executivo')
bcrypt = Bcrypt()