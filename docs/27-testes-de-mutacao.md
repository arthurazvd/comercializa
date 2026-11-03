# Plano e execução de Testes de Mutação

## Objetivo

Avaliar a **capacidade dos testes de detectar defeitos**. Cobertura de linhas elevada não garante eficácia: o teste de mutação modifica propositalmente pequenas regras e observa se algum teste reprova.

## Escopo e ferramenta

- **Ferramenta:** `mutmut` 2.5.1 (Python, versão fixada para testes Django).
- **Escopo piloto:** `backend/core/services.py` (cálculos e dashboard/SAD) e `backend/core/stock_lots.py` (estoque por lote), configurados em `backend/pyproject.toml`.
- **Testes executados:** `backend/tests/` com `pytest`; o banco de teste deve ser isolado, usando `DEBUG=True` e SQLite local.
- **Não estão no escopo inicial:** frontend e outras partes do backend. Ampliar progressivamente após interpretar mutantes sobreviventes.

## Método

1. Garantir que todos os testes de referência passem.
2. Criar mutantes (alterações em operações, expressões e condições) com `mutmut`.
3. Executar os testes para cada mutante e classificar: **morto** (teste detectou), **sobrevivente** (teste não detectou), **timeout/inválido** (analisar separadamente).
4. Registrar os resultados e criar novos testes para mutantes sobreviventes que representem defeitos reais.
5. Repetir os testes normais e a mutação; anexar evidências e relacionar a issue/PR ao milestone **Testes de Mutação**.

**Indicador:** taxa de mutação = mutantes mortos ÷ (mortos + sobreviventes) × 100, excluindo mutantes tecnicamente inválidos após revisão. Não confundir com **cobertura de código mínima de 70%**. Não há taxa de mutação medida ou inventada nesta entrega.

## Executar localmente (Linux / WSL)

> A versão 3.x apresentou no GitHub Actions **156 testes aprovados, mas zero testes associados aos mutantes** (problema de importação/instrumentação em projeto Django). A configuração atual fixa `mutmut==2.5.1`, que aplica a mutação no arquivo original durante a execução e o restaura. Execute em Linux/WSL ou no GitHub Actions, em branch de trabalho e sem mudanças locais não commitadas. Essa correção ainda depende da execução no CI para validação.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-mutation.txt
python -m pytest tests --no-cov -q
mutmut run
mutmut results
# opcional: investigação interativa
mutmut show all
# opcional: relatório XML para evidência
mutmut junitxml > mutation-results.xml
```

**GitHub Actions:** abra **Actions → Testes de mutação (sob demanda) → Run workflow** na branch de trabalho. O primeiro push em `feature/testes-mutacao` também dispara esse job; o botão manual fica disponível após o workflow ser incorporado à branch padrão. O job mantém resultado e eventuais artefatos; uma execução de mutação pode levar mais tempo que a suíte habitual. O `mutmut` não é acionado a cada push para não bloquear alterações comuns por seu custo computacional.

## Registro da execução nas aulas

Preencher uma linha **somente depois da execução real**, anexando link do job GitHub e captura/relatório quando possível:

| Data da aula | Commit / branch | Total válido | Mortos | Sobreviventes | Taxa | Evidência (URL) |
|---|---|---:|---:|---:|---:|---|
| *a preencher* | *a preencher* | — | — | — | — | — |

**Critério de encerramento do milestone:** baseline verde, relatório da primeira execução de mutação, registro de sobreviventes relevantes, pelo menos uma melhoria de teste documentada se houver sobreviventes e PR concluído via GitFlow.

## Riscos e cuidados

- Nunca rodar contra a base Neon de produção. Garanta que `DATABASE_URL` não esteja definido na sessão usada nos testes.
- Falhas de `mutmut` por configuração devem ser corrigidas antes de tratar scores como evidência válida. A execução anterior com 156 testes aprovados NÃO produziu taxa de mutação válida.
- Mutantes equivalentes à lógica original precisam de análise e justificativa; resultados automáticos não são prova de qualidade isoladamente.

Ver também [Plano de Testes](07-plano-de-testes.md), [CI e GitFlow](29-ci-sonarqube-gitflow.md) e [Manual de Execução](28-manual-de-execucao.md).
