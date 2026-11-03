# Comercializa

Sistema web para a gestão de lojas de variedades, com **cadastro de produtos**, fotos, estoque por lote, vendas e estornos, relatórios financeiros e painel de apoio à decisão.

**Tecnologias:** Django + Django REST Framework (API), Vue 3 + Vite (interface), SQLite (desenvolvimento) e PostgreSQL/Neon (produção).

## Funcionalidades

- Catálogo com SKU, descrição, categoria e foto; controle de estoque e validade por lote.
- Registro de vendas, descontos, movimentações de estoque e estornos auditáveis.
- Custo histórico por lote, margem e indicadores financeiros; exportação para Excel.
- Dashboard de vendas, produtos mais vendidos e alertas de reposição/validade.
- Interface responsiva, login por token e rotas próprias para as principais páginas.

## Rodar localmente

**Requisitos:** Python 3.12, Node.js 22 e npm. Abra dois terminais na raiz do repositório.

**Terminal 1 — API:**

```bash
cd backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Terminal 2 — interface:**

```bash
cd frontend
npm ci
npm run dev
```

Abra **http://localhost:5173**. A API local fica em **http://127.0.0.1:8000/api/**. Para criar dados fictícios, execute `python manage.py seed_demo` **somente em desenvolvimento**.

Para instalar, configurar usuários/ambientes, publicar ou resolver problemas, consulte o **[Manual de Execução](docs/28-manual-de-execucao.md)**.

## Testes, cobertura e SonarQube

A CI executa os testes do backend e do frontend, valida o build e exige **cobertura mínima de 70% do backend**. A análise SonarQube está configurada na mesma pipeline; é necessário configurar os secrets do projeto. A execução manual de análise também está disponível nos dias de aula.

```bash
cd backend
python -m pytest tests --cov=core --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=70
```

```bash
cd frontend
npm ci && npm test && npm run build
```

[GitHub Actions](https://github.com/arthurazvd/comercializa/actions) · [Configuração CI/SonarQube](docs/29-ci-sonarqube-gitflow.md) · [Plano de Testes](docs/07-plano-de-testes.md) · [Testes de Mutação](docs/27-testes-de-mutacao.md)

## Documentação

- [Índice completo da documentação](docs/00-indice.md)
- [Visão e requisitos](docs/01-visao-do-projeto.md) · [Casos de uso](docs/03-casos-de-uso.md)
- [Plano de Testes](docs/07-plano-de-testes.md) · [Cobertura e evidências](docs/13-estado-atual-testes.md)
- [Testes de Mutação com mutmut](docs/27-testes-de-mutacao.md)
- [Manual de Execução do Projeto](docs/28-manual-de-execucao.md)
- [GitFlow, milestone e SonarQube](docs/29-ci-sonarqube-gitflow.md)
- [Evidências e validação desta entrega](docs/30-validacao-e-evidencias.md)

## Repositório e contribuições

[github.com/arthurazvd/comercializa](https://github.com/arthurazvd/comercializa) · Desenvolvimento em `feature/*` a partir de `develop`, por Pull Request. `main` representa código publicado. Veja o [fluxo de contribuição](docs/29-ci-sonarqube-gitflow.md).
