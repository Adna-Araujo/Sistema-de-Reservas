import click
from flask.cli import with_appcontext

# Importações Locais
from .extensions import db, bcrypt
from .models import Usuario

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin(username, email, password):
    """Cria um novo usuário administrador."""
    
    # Verifica se o usuário já existe
    if Usuario.query.filter_by(username=username).first():
        click.echo(f"Erro: Usuário '{username}' já existe.")
        return

    # 1. Cria o hash da senha
    # O .decode('utf-8') garante que o hash seja salvo como string (Unicode) no BD
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # 2. Cria o objeto Usuario, definindo is_admin=True
    admin_user = Usuario(
        username=username,
        email=email,
        password=hashed_password,
        is_admin=True # CHAVE: Define o usuário como administrador
    )
    
    # 3. Adiciona e salva no banco de dados
    try:
        db.session.add(admin_user)
        db.session.commit()
        click.echo(f" Administrador '{username}' criado com sucesso!")
    except Exception as e:
        db.session.rollback()
        click.echo(f" Erro ao criar administrador: {e}")

def init_cli(app):
    """Registra comandos CLI no aplicativo Flask."""
    app.cli.add_command(create_admin)