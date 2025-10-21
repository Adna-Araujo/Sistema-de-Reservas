# Importações
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateTimeField, IntegerField # <-- ADICIONADO IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange # <-- ADICIONADO NumberRange
from .models import Usuario, Reserva, Room
from .extensions import db

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
    inicio = DateTimeField('Data e Hora de Início', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])

    # Duração em horas (1 a 4 horas)
    duracao = SelectField('Duração (horas)',
                          choices=[(str(i), f'{i} hora(s)') for i in range(1, 5)],
                          validators=[DataRequired()])

    submit = SubmitField('Fazer Reserva')

    def __init__(self, sala_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

# ======================
# Formulário de Gestão de Sala (NOVO)
# ======================
class RoomForm(FlaskForm):
    name = StringField('Nome da Sala', validators=[DataRequired(), Length(min=2, max=100)])
    description = StringField('Descrição (opcional)', validators=[Length(max=200)])
    capacity = IntegerField('Capacidade (Pessoas)', 
                            validators=[DataRequired(), NumberRange(min=1, message='A capacidade deve ser no mínimo 1.')])
    is_active = BooleanField('Sala Ativa (Disponível para Reservas)', default='checked')
    submit = SubmitField('Salvar Sala')
    
    # Validação customizada para garantir que o nome da sala seja único (exceto ao editar a própria sala)
    def validate_name(self, name):
        # O self.room_id será definido no main.py se estivermos editando
        room_id = getattr(self, 'room_id', None)
        
        query = Room.query.filter_by(name=name.data)
        
        if room_id:
            # Exclui a sala atual da checagem de unicidade
            query = query.filter(Room.id != room_id)
            
        existing_room = query.first()
        
        if existing_room:
            raise ValidationError('Já existe uma sala com este nome. Escolha um nome diferente.')


# Você pode remover a importação 'from email_validator import validate_email, EmailNotValidError' 
# se não a estiver usando diretamente para simplificar as importações, mas não é obrigatório.