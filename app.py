from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt # <== NOVO
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required # <== NOVO
from forms import RegistrationForm, LoginForm # <== NOVO: Criaremos forms.py em seguida


# 1. Cria a instância do aplicativo
app = Flask(__name__)

# Configuração de chave secreta (OBRIGATÓRIA para Flask e sessões)
# Em um ambiente real, este valor viria de variáveis de ambiente.
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura-e-longa-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app) # <== NOVO
login_manager = LoginManager(app) # <== NOVO

# Diz ao Flask-Login qual rota de login ele deve usar
login_manager.login_view = 'login' 
login_manager.login_message_category = 'info' # Categoria para mensagens de erro/aviso

class Usuario(db.Model, UserMixin): # <== ADICIONADO UserMixin
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    # Relação com Reservas
    reservas = db.relationship('Reserva', backref='autor', lazy=True) # <== ADICIONADO: 'autor' será o apelido do usuário que criou a reserva

    def __repr__(self):
        return f"Usuário('{self.username}', '{self.email}')"

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

# 2. Define a Rota Principal (Homepage)
@app.route('/')
def index():
    # Agora renderizamos o arquivo index.html, passando uma variável de exemplo (status)
    return render_template('index.html', status="Estrutura de Templates OK!")

# ROTA DE LOGIN
@app.route("/login", methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para a home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Usuario.query.filter_by(email=form.email.data).first()
        
        # Checa se o usuário existe E se a senha criptografada confere
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data) # Usa Flask-Login
            
            # Pega o parâmetro 'next' da URL (se o usuário tentou acessar uma página protegida antes)
            next_page = request.args.get('next')
            
            flash('Login bem-sucedido!', 'success')
            
            # Redireciona para a página 'next' ou para a página inicial
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Login sem sucesso. Por favor, verifique email e senha.', 'danger')
            
    return render_template('login.html', title='Login', form=form)

# ROTA DE LOGOUT
@app.route("/logout")
def logout():
    logout_user() # Função Flask-Login para remover usuário da sessão
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('index'))

# ROTA DE CADASTRO
@app.route("/register", methods=['GET', 'POST'])
def register():
    # Se o usuário já estiver logado, redireciona para a home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = RegistrationForm()
    
    # Se o formulário for submetido e validado (incluindo validações do BD)
    if form.validate_on_submit():
        # Criptografa a senha antes de salvar no banco de dados
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        user = Usuario(username=form.username.data, email=form.email.data, password=hashed_password)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Conta criada para {form.username.data}! Agora você pode fazer login.', 'success')
        
        return redirect(url_for('login'))
        
    return render_template('register.html', title='Cadastro', form=form)

# 3. Bloco principal para rodar o aplicativo
if __name__ == '__main__':
    # O 'debug=True' permite recarregamento automático durante o desenvolvimento
    app.run(debug=True, host='0.0.0.0')