# 1. Importa create_app (presumido em __init__.py ou __main__.py)
# 2. Importa db (presumido em extensions.py)
from . import create_app 
from .extensions import db 
# 3. Importa modelos
from .models import Usuario, Reserva, Room
from flask_bcrypt import generate_password_hash 
# ----------------------------------------------------

from datetime import datetime, timedelta, time
import random
from faker import Faker

# ----------------------------------------------------

# --- Inicialização do App FORA do escopo 'with app.app_context()' ---
app = create_app()

# ----------------------------------------------------
# 1. Configuração do Faker e Parâmetros
# ----------------------------------------------------
fake = Faker('pt_BR')  # Inicializa o Faker
NUM_RESERVAS = 350     # Quantidade total de reservas a serem criadas
DIAS_ATRAS = 30        # Período de 14 dias atrás até hoje

from reservas.models import Room, Reserva, db
from reservas import create_app, db

def popular_salas():
    with app.app_context():
        # Lista de salas temáticas de Escape Room
        salas_temas = [
            {'name': 'Laboratório Zumbi', 'capacity': 6},
            {'name': 'Assalto ao Banco', 'capacity': 5},
            {'name': 'Cativeiro do Serial Killer', 'capacity': 4},
            {'name': 'O Mistério da Pirâmide', 'capacity': 8}
        ]

        for sala in salas_temas:
            # Verifica se a sala já existe para não duplicar
            if not Room.query.filter_by(name=sala['name']).first():
                nova_sala = Room(name=sala['name'], capacity=sala['capacity'])
                db.session.add(nova_sala)
        
        db.session.commit()
        print("✅ Salas temáticas criadas com sucesso!")

if __name__ == "__main__":
    popular_salas()
    # Chame sua função de reservas logo abaixo aqui...
with app.app_context():
    
    # ----------------------------------------------------
    # A. SEEDING DE SALAS (Mantido o seu código original e garantindo que não duplique)
    # ----------------------------------------------------
    if not db.session.query(Room).first():
        salas = [
            Room(name='Sala 101', description='Sala climatizada com projetor', capacity=10),
            Room(name='Sala 102', description='Espaço amplo para reuniões', capacity=15),
            Room(name='Quarto Deluxe', description='Suíte com vista para o mar', capacity=2),
        ]
        db.session.add_all(salas)
        db.session.commit()
        print("✅ Salas iniciais adicionadas ao banco!")
    
    todas_salas = db.session.query(Room).all()

    # ----------------------------------------------------
    # B. SEEDING DE USUÁRIO (Garantir um usuário para as reservas)
    # ----------------------------------------------------
    # Tenta obter um usuário admin existente ou cria um novo
    usuario_admin = db.session.query(Usuario).filter_by(email='teste@sistema.com').first()
    if not usuario_admin:
        hashed_password = generate_password_hash("senha123").decode('utf-8')
        usuario_admin = Usuario(
            username='admin_teste',
            email='teste@sistema.com',
            password=hashed_password,
            is_admin=True
        )
        db.session.add(usuario_admin)
        db.session.commit()
        print("✅ Usuário 'admin_teste' criado (senha: senha123).")
    else:
        print("ℹ️ Usuário 'admin_teste' já existe.")

    # ----------------------------------------------------
    # C. SEEDING DE RESERVAS DE TESTE (14 dias)
    # ----------------------------------------------------
    if db.session.query(Reserva).count() < NUM_RESERVAS:
        
        reservas = []
        data_inicio_geracao = datetime.now() - timedelta(days=DIAS_ATRAS)
        
        for i in range(NUM_RESERVAS):
            # 1. Escolhe uma sala e um dia aleatoriamente
            sala_escolhida = random.choice(todas_salas)
            
            dia_reserva = fake.date_time_between(
                start_date=data_inicio_geracao, 
                end_date="now",
                tzinfo=None
            ).date()
            
            # Define horas comuns (ex: entre 8h e 17h)
            hora_inicio = random.randint(8, 17)
            # Duração de 1 a 2 horas
            duracao = random.choice([timedelta(hours=1), timedelta(hours=1, minutes=30), timedelta(hours=2)])
            
            # Cria o objeto datetime de início
            start_time = datetime.combine(dia_reserva, time(hour=hora_inicio, minute=random.choice([0, 30])))
            end_time = start_time + duracao

            # Ajuste de segurança para garantir que o fim não ultrapasse 19h
            if end_time.hour >= 19:
                end_time = datetime.combine(dia_reserva, time(hour=19, minute=0))
                if end_time <= start_time: continue # Pula se for inválido mesmo após ajuste

            nova_reserva = Reserva(
                client_name=fake.catch_phrase(),
                start_time=start_time,
                end_time=end_time,
                room_id=sala_escolhida.id,
                user_id=usuario_admin.id
            )
            reservas.append(nova_reserva)
            
        db.session.add_all(reservas)
        db.session.commit()
        
        print(f"✅ Seeadura de reservas concluída! {len(reservas)} reservas criadas nos últimos {DIAS_ATRAS} dias.")
    else:
        print(f"ℹ️ Já existem {db.session.query(Reserva).count()} reservas. Seeding de reservas ignorado.")