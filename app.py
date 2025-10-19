from flask import Flask, render_template

# 1. Cria a instância do aplicativo
app = Flask(__name__)

# Configuração de chave secreta (OBRIGATÓRIA para Flask e sessões)
# Em um ambiente real, este valor viria de variáveis de ambiente.
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-segura-e-longa-12345'


# 2. Define a Rota Principal (Homepage)
@app.route('/')
def index():
    # Agora renderizamos o arquivo index.html, passando uma variável de exemplo (status)
    return render_template('index.html', status="Estrutura de Templates OK!")
# Rotas TEMPORÁRIAS para evitar erros de URL_FOR na Fase 1
@app.route('/login')
def login():
    return "Página de Login em construção (Fase 3)"

@app.route('/reservar')
def reservar():
    return "Página de Reservas em construção (Fase 4)"

# 3. Bloco principal para rodar o aplicativo
if __name__ == '__main__':
    # O 'debug=True' permite recarregamento automático durante o desenvolvimento
    app.run(debug=True, host='0.0.0.0')