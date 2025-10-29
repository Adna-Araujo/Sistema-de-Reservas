# Importa a função de criação da aplicação do pacote 'reservas' (ou seja, de __init__.py)
from reservas import create_app

# ======================
# Instância global e Execução
# ======================
# Chama a função que cria e configura o app Flask
app = create_app() 

if __name__ == '__main__':
    # Inicia o servidor de desenvolvimento
    app.run(debug=True)