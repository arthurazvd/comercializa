# Manual de Execução — Comercializa

## 1. Pré-requisitos

- Python **3.12** e Node.js **22** com npm.
- Git e terminal (PowerShell/CMD ou Linux/macOS).
- Banco **SQLite** no desenvolvimento. Neon/PostgreSQL é usado na produção com Render.
- Clonar `https://github.com/arthurazvd/comercializa` ou extrair o ZIP em uma pasta.

## 2. Executar backend Django

Na raiz do projeto:

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual:

| Sistema | Comando |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Linux/macOS/WSL | `source .venv/bin/activate` |

Depois:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

A API deve responder em `http://127.0.0.1:8000/api/health/` e o painel Django (se habilitado) em `http://127.0.0.1:8000/admin/`.

**Login local:** com `DEBUG=True` (padrão sem variáveis), os endpoints de negócio funcionam sem autenticação para desenvolvimento. Para criar o administrador do Django, use `python manage.py createsuperuser` (banco local). A configuração de produção é diferente.

**Dados fictícios (opcional):** rode `python manage.py seed_demo` apenas no banco de desenvolvimento. Nunca executar seed, `flush` ou `migrate` destrutivo no Neon de produção sem backup e análise.

## 3. Executar frontend Vue

Em outro terminal, a partir da raiz:

```bash
cd frontend
npm ci
npm run dev
```

Navegue em `http://localhost:5173`. Durante o desenvolvimento, o Vite encaminha `/api` para `http://127.0.0.1:8000` (configuração de `frontend/vite.config.js`). Em produção, configure `VITE_API_URL` com a URL pública da API, incluindo `/api/`.

## 4. Testes automatizados

### Backend (mínimo 70%)

```bash
cd backend
python -m pytest tests --cov=core --cov-report=term-missing --cov-report=xml:coverage.xml --cov-fail-under=70
```

Comandos opcionais: `python -m pytest tests --no-cov -q` e `python -m pytest tests --cov=core --cov-report=html --cov-fail-under=70`; no segundo, abra `backend/htmlcov/index.html`.

### Frontend

```bash
cd frontend
npm ci
npm test
npm run build
```

### Mutação (Linux/WSL)

```bash
cd backend
python -m pip install -r requirements-mutation.txt
mutmut run
mutmut results
```

Consulte [Testes de Mutação](27-testes-de-mutacao.md) para configuração e interpretação. Os mutantes não são executados contra o banco de produção.

## 5. GitHub Actions e SonarQube

O workflow `.github/workflows/tests.yml` executa testes frontend, build, pytest com gate de 70%, publica `coverage.xml` como artefato e chama o SonarQube. A análise SonarQube exige `SONAR_TOKEN` e `SONAR_HOST_URL` em **Settings → Secrets and variables → Actions → Repository secrets**. O servidor SonarQube precisa aceitar conexões do GitHub Actions.

**Nas aulas:** acesse **Actions → Testes, cobertura e SonarQube → Run workflow**, selecione a branch desejada e registre o link e o resultado em `docs/29-ci-sonarqube-gitflow.md` ou na issue do milestone. O workflow também roda automaticamente em commits e PRs. Para mutação, selecione o workflow manual correspondente.

## 6. Publicação (resumo)

- **Backend:** Render, com `rootDir=backend` e `render.yaml`, variáveis sensíveis configuradas fora do repositório: `SECRET_KEY`, `DATABASE_URL` (Neon), `CORS_ALLOWED_ORIGINS` e credenciais iniciais. O `backend/build.sh` executa migrações.
- **Frontend:** Cloudflare Pages com variável `VITE_API_URL` apontando para a API do Render, Node 22, build `npm ci && npm run build`, diretório de saída `frontend/dist` (se a raiz for o repositório).
- Faça backup do Neon antes de aplicar novas migrações e atualize **backend antes de frontend** quando a API/modelo mudar.
- Confirme GitHub Actions verde, deploys concluídos, login, cadastro, estoque, vendas, gráficos e exportação. Nunca versionar `.env`, tokens ou senhas.

## 7. Solução de problemas

| Sintoma | Verificação |
|---|---|
| `npm ci` falha | Use Node 22, confirme se o lockfile foi commitado e procure o pacote com erro no log do Actions. |
| `ModuleNotFoundError` | Ambiente `.venv` ativo e `pip install -r requirements.txt` concluído. |
| `pytest` retorna falhas | Não desative testes; leia o nome do teste e o traceback. |
| Cobertura abaixo de 70% | Adicione testes para os caminhos apontados em `term-missing`; não exclua arquivos apenas para elevar a taxa. |
| SonarQube falha | Configure URL/token do servidor, projeto `comercializa`, acesso da rede GitHub e permissões. |
| Frontend sem API | Confira `VITE_API_URL`, deploy do Render, `CORS_ALLOWED_ORIGINS` e Network do navegador. |
| Rota `/estoque` dá 404 ao atualizar | Configure fallback SPA no Cloudflare Pages; veja `frontend/public/_redirects`. |

## 8. Evidências para entrega acadêmica

Links do repositório, PR com branch `feature/*`, milestone, Actions verde, relatório de cobertura >=70%, análise SonarQube em aula e relatório de mutação. Inclua data/commit em cada evidência.

[Voltar ao README](../README.md) · [Plano de Testes](07-plano-de-testes.md) · [GitFlow/SonarQube](29-ci-sonarqube-gitflow.md)
