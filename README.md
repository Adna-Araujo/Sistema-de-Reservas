Sistema de Reservas
[imagem aqui]

O Sistema de Reservas é uma aplicação Full Stack desenvolvida para automatizar o agendamento de serviços e o gerenciamento administrativo. O projeto foca em uma experiência fluida para o cliente e um controle centralizado para o administrador, utilizando um banco de dados integrado para persistência de informações.

Sobre o Projeto
Este projeto foi criado para resolver a necessidade de organização em fluxos de agendamentos manuais. A aplicação permite que usuários visualizem horários e realizem reservas, enquanto fornece ao administrador uma interface para controle total do fluxo de trabalho.

Funcionalidades Principais
Área do Cliente:

Interface para realização de novos agendamentos.

Confirmação visual após a conclusão da reserva.

Área Administrativa:

Dashboard para visualização de todas as reservas cadastradas.

Gestão de dados: edição e exclusão de reservas e clientes.

Acompanhamento de métricas de agendamentos por período.

[imagem aqui]

Tecnologias Utilizadas
Linguagem: Python 3.x

Framework Web: Flask

Banco de Dados: SQLite

Frontend: HTML5 e CSS3

Como Executar o Projeto
Clone o repositório do projeto em sua máquina local.

Crie um ambiente virtual com o comando: python -m venv .venv

Ative o ambiente virtual:

No Windows: .venv\Scripts\activate

No Linux/Mac: source .venv/bin/activate

Instale as dependências necessárias: pip install flask

Inicie a aplicação: python -m reservas

Acesse o endereço http://127.0.0.1:5000 no seu navegador.

[imagem aqui]

Estrutura do Diretório
static/: Arquivos de estilização e imagens.

templates/: Páginas HTML divididas entre área pública e administrativa.

.venv/: Ambiente virtual do projeto.

reservas.py/: Arquivo principal com a lógica de rotas e execução.

database.db/: Arquivo do banco de dados SQLite.

Roadmap de Melhorias
Implementação de sistema de autenticação para a área administrativa.

Integração com serviço de envio de e-mails para notificações.

Adição de calendário interativo no frontend para seleção de datas.