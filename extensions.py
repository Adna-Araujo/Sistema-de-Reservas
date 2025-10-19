from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# ====================================================================
# INSTÂNCIAS GLOBAIS
# Estas são definidas aqui para serem importadas por models.py e app.py,
# evitando a importação circular.
# ====================================================================

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
