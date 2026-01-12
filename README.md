🚪 Sistema de Reservas - EscapingRooms
O EscapingRooms é uma aplicação Full Stack desenvolvida para automatizar o agendamento de sessões de Escape Room e o gerenciamento administrativo. O projeto foca em uma experiência imersiva para o cliente e um controle centralizado para o administrador, utilizando um banco de dados relacional integrado.

📝 Sobre o Projeto
Este projeto foi criado para resolver a necessidade de organização em fluxos de agendamentos complexos. A aplicação permite que usuários visualizem salas temáticas e realizem reservas, enquanto fornece ao administrador um painel de controle (ERP) para gerenciar o fluxo de trabalho, monitorar a ocupação das salas e analisar o desempenho do negócio.

✨ Funcionalidades Principais
👤 Área do Cliente
Landing Page Imersiva: Interface moderna em Dark Mode com cards dinâmicos para cada sala temática.

Visualização de Salas: Informações de capacidade e temática puxadas diretamente do banco de dados.

Fluxo de Reserva: Botões de ação rápida para agendamento por categoria.

🔐 Área Administrativa (Flask-Admin)
Dashboard de Métricas: Cards com contagem total de reservas e salas ativas.

Relatório de Desempenho: Gráficos diários de agendamentos utilizando Chart.js.

Gestão de Inventário: Controle total sobre salas (Rooms), Usuários e Reservas (CRUD completo).

Exportação de Dados: Funcionalidade de exportação de relatórios em formato CSV.

🛠️ Tecnologias Utilizadas
Linguagem: Python 3.12

Framework Web: Flask

Banco de Dados: SQLite com SQLAlchemy (ORM)

Painel Admin: Flask-Admin com interface Bootstrap 4

Segurança: Flask-Login para autenticação de administradores

Visualização de Dados: Chart.js

🚀 Como Executar o Projeto
Clone o repositório em sua máquina local.

Crie um ambiente virtual: python -m venv .venv

Ative o ambiente virtual:

Windows: .venv\Scripts\activate

Linux/Mac: source .venv/bin/activate

Instale as dependências: pip install -r requirements.txt

Popule o Banco de Dados (Seed): (Gera automaticamente 8 salas e 550 reservas para teste)

Bash

python -m reservas.seed
Inicie a aplicação: python -m reservas

Acesse http://127.0.0.1:5000 para o site ou http://127.0.0.1:5000/admin para a gestão.

📁 Estrutura do Diretório
reservas/: Pacote principal da aplicação.

static/: Arquivos CSS, ícones e scripts de gráficos.

templates/: Páginas HTML (JinJa2) divididas entre área pública e administrativa.

models.py: Definição das tabelas relacional (Salas x Reservas x Usuários).

seed.py: Script de automação de dados em massa.

🗺️ Roadmap de Melhorias
[x] Implementação de sistema de autenticação administrativa.

[x] Geração de dados de teste massivos para análise de performance.

[ ] Integração com serviço de envio de e-mails para confirmação.

[ ] Adição de calendário interativo no frontend para seleção de horários.