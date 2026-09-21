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

O projeto utiliza **pytest**, **pytest-django** e **pytest-cov**. Há testes
unitários do CRUD de produtos em `backend/tests/test_product_service.py`. Eles
usam `unittest.mock` para substituir o acesso ao banco e verificar as operações
de inserir, consultar, atualizar e excluir de forma isolada.

Os testes de integração estão em `backend/tests/test_api.py`. Eles fazem
requisições HTTP à API com `APIClient` e verificam, junto ao banco de testes, se
as rotas, os serializers e os modelos funcionam em conjunto.

Para instalar as dependências e executar todos os testes:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
```

O próprio comando `pytest` gera:

- o resumo dos testes no terminal;
- o relatório navegável em `backend/htmlcov/index.html`;
- o arquivo `backend/coverage.xml`, compatível com o SonarQube.

Na execução validada desta versão, os **73 testes passaram** e a cobertura
total obtida foi de **80%**.

Teste de unidade verifica uma função isoladamente, substituindo dependências
por mocks. Teste de integração verifica a comunicação entre partes reais do
sistema, como rota, serializer, modelo e banco de dados de teste.

### Experiência com os testes

A implementação dos testes ajudou a confirmar separadamente as quatro operações
do CRUD e também o fluxo completo da API. Os mocks tornaram os testes unitários
rápidos e independentes do banco. Já os testes de integração deram mais
segurança de que as requisições realmente persistem e recuperam os dados como
esperado.

### Tutorial utilizado

- [Django REST Framework: Quickstart](https://www.django-rest-framework.org/tutorial/quickstart/): apresenta a criação de uma API CRUD com serializers, viewsets, rotas e testes automatizados usando as ferramentas de teste do Django.

### Integração contínua

O workflow `.github/workflows/tests.yml` instala as dependências, executa os
testes, calcula a cobertura e disponibiliza os relatórios como artefatos no
GitHub Actions a cada push ou pull request.

Consulte também o [plano de testes](docs/07-plano-de-testes.md).
