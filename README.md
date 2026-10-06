# Comercializa

Sistema de Apoio à Decisão (SAD) para pequenos comércios.

O repositório foi separado em:

- `backend/`: API em Django + Django REST Framework.
- `frontend/`: interface em Vue 3 + Vite.
- `docs/`: documentação do projeto, requisitos, visão, arquitetura, SAD e testes.

## Escopo desta primeira versão

A versão inicial já permite:

- cadastrar, editar, listar e excluir produtos;
- controlar estoque, estoque mínimo e validade;
- registrar vendas com múltiplos itens;
- baixar o estoque automaticamente após uma venda;
- visualizar faturamento e quantidade de vendas;
- visualizar produtos mais vendidos;
- identificar produtos com estoque crítico;
- identificar produtos com baixa movimentação;
- identificar produtos próximos do vencimento;
- gerar recomendações iniciais de reposição e promoção.

A parte de CRUD existe principalmente para gerar os dados usados pelo módulo de apoio à decisão.

## Tecnologias

### Backend
- Python
- Django
- Django REST Framework
- SQLite

### Frontend
- Vue 3
- Vite
- Axios

## Como executar

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`

### 2. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173`

## Testes

```bash
cd backend
python manage.py test
```

Consulte também `docs/07-plano-de-testes.md`.

## Equipe

- Arthur Azevêdo

## Documentação

A documentação completa está disponível em [`docs/00-indice.md`](docs/00-indice.md).

Documentos principais do Projeto 01:

- [Documento de Visão](docs/01-visao-do-projeto.md)
- [Product Backlog — User Stories](docs/11-user-stories.md)
- [Plano Geral de Iterações](docs/12-plano-iteracoes.md)
- [Relatório do Estado Atual dos Testes](docs/13-estado-atual-testes.md)
- [Plano da Iteração 1](docs/14-iteracao-01.md)
