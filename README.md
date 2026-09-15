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
