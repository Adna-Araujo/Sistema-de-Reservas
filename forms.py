# Importações
from datetime import datetime, date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

# Para a validação de email (necessita de `pip install email-validator`)
from email_validator import validate_email, EmailNotValidError

# Importa a classe Usuario do modelo, que agora está em `models.py`
from models import Usuario, Reserva, Room


# --- Formulário de Cadastro (RegistrationForm) ---
class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Senha', 
                             validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Escolha outro.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está cadastrado. Faça o login ou use outro e-mail.')
        
# --- Formulário de Login (LoginForm) ---
class LoginForm(FlaskForm):
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Senha', 
                             validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login')

# --- Formulário de Reserva (ReservaForm) - Novo da Fase 3 ---
class ReservaForm(FlaskForm):
    # Lista de salas de exemplo (Você pode expandir isso)
    SALAS = [
        ('Sala 1', 'Sala de Reunião Alpha (Capacidade 10)'),
        ('Sala 2', 'Sala de Treinamento Beta (Capacidade 25)'),
        ('Sala 3', 'Sala de Conferência Gamma (Capacidade 50)')
    ]

    sala = SelectField('Sala de Reunião', choices=SALAS, validators=[DataRequired()])
    
    # Validação para garantir que a data seja hoje ou no futuro
    data = DateField('Data da Reserva', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Campo de Hora
    hora = StringField('Hora (HH:MM)', validators=[DataRequired(), Length(min=5, max=5)]) # Usamos StringField e validaremos o formato HH:MM
    
    # Duração da Reserva em Horas (opcional)
    duracao = SelectField('Duração (horas)', choices=[(str(i), f'{i} hora(s)') for i in range(1, 5)], validators=[DataRequired()])
    
    submit = SubmitField('Fazer Reserva')

    def validate_data(self, data):
        if data.data < date.today():
            raise ValidationError('A data da reserva não pode ser no passado.')
