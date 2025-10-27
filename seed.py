from reservas.__main__ import app, db
from models import Room

with app.app_context():
    salas = [
        Room(name='Sala 101', description='Sala climatizada com projetor', capacity=10),
        Room(name='Sala 102', description='Espaço amplo para reuniões', capacity=15),
        Room(name='Quarto Deluxe', description='Suíte com vista para o mar', capacity=2),
    ]

    db.session.add_all(salas)
    db.session.commit()
    print(" Salas iniciais adicionadas ao banco!")
