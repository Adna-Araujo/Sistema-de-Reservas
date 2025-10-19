# Importações
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import Usuario, Reserva, Room

# Para validação de email
from email_validator import validate_email, EmailNotValidError

# ======================
# Formulário de Cadastro
# ======================
class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

    def validate_username(self, username):
        user = Usuario.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso. Escolha outro.')

    def validate_email(self, email):
        user = Usuario.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este e-mail já está cadastrado. Faça o login ou use outro e-mail.')

# ======================
# Formulário de Login
# ======================
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField('Lembrar-me')
    submit = SubmitField('Login')

# ======================
# Formulário de Reserva
# ======================
class ReservaForm(FlaskForm):
    # Campo para selecionar a sala dinamicamente do banco
    sala = SelectField('Sala de Reunião', coerce=int, validators=[DataRequired()])

    # Data e hora de início da reserva
    inicio = DateTimeField('Data e Hora de Início', format='%Y-%m-%d %H:%M', validators=[DataRequired()])

    # Duração em horas (1 a 4 horas)
    duracao = SelectField('Duração (horas)',
                          choices=[(str(i), f'{i} hora(s)') for i in range(1, 5)],
                          validators=[DataRequired()])

    submit = SubmitField('Fazer Reserva')

    def __init__(self, sala_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
