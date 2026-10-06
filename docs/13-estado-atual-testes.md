# Relatório do Estado Atual dos Testes

## 1. Objetivo

Este documento registra o **baseline de qualidade do Comercializa antes das evoluções planejadas para o Projeto 01 da disciplina de Teste de Software**, identificando os testes existentes, a cobertura observada e os principais débitos técnicos.

## 2. Ambiente e ferramentas

O backend utiliza:

- Python e Django;
- Django REST Framework;
- `pytest`;
- `pytest-django`;
- `pytest-cov`;
- `factory-boy`.

A configuração está centralizada em `backend/pytest.ini`, com descoberta dos testes em `backend/tests/` e geração de cobertura do módulo `core`.

## 3. Testes existentes

O sistema **não é um legado sem testes**. Antes desta entrega já existia uma suíte automatizada organizada nos seguintes arquivos:

| Arquivo | Classificação predominante | Objetivo |
|---|---|---|
| `backend/tests/test_models.py` | Unidade | Validar modelos, cálculos e regras básicas de domínio. |
| `backend/tests/test_api.py` | Integração/API | Validar endpoints, persistência e comportamento das operações via API. |
| `backend/tests/test_sad.py` | Unidade/integração | Validar serviços, regras, recomendações e respostas do módulo SAD. |
| `backend/tests/test_acceptance.py` | Aceitação | Validar fluxos representativos do sistema sob uma perspectiva funcional. |
| `backend/tests/conftest.py` | Suporte | Disponibilizar fixtures compartilhadas. |
| `backend/tests/factories.py` | Suporte | Gerar dados de teste com `factory-boy`. |

Portanto, há testes de **unidade, integração/API e aceitação**, além de testes específicos das regras do SAD.

## 4. Estado da suíte

No baseline já aferido do projeto, a execução automatizada apresentou:

- **73 testes aprovados**;
- **0 falhas** na execução registrada;
- **72% de cobertura** do código do backend analisado.

A cobertura é gerada com `pytest-cov`. O comando recomendado para reproduzir a medição é:

```bash
cd backend
pytest tests/ --cov=core --cov-report=term-missing --cov-report=html
```

O relatório HTML é gerado em `backend/htmlcov/index.html`.

> Os números acima representam o baseline registrado antes das novas atividades da disciplina. A cobertura deve ser medida novamente ao final das iterações para permitir comparação objetiva da evolução.

## 5. Pontos positivos identificados

- suíte automatizada já existente;
- separação entre testes de modelos, API, SAD e aceitação;
- uso de factories e fixtures para reduzir duplicação;
- medição automatizada de cobertura;
- testes de regras importantes, como cálculo de valores, estoque e recomendações;
- estrutura preparada para execução repetível com `pytest`.

## 6. Débitos técnicos e lacunas

Mesmo com testes existentes, foram identificados os seguintes pontos de melhoria:

1. **Cobertura ainda incompleta:** 72% indica que há caminhos do backend sem verificação automatizada.
2. **Frontend sem suíte equivalente documentada:** a maior concentração de testes está no backend.
3. **Ausência de E2E completo no navegador:** os testes de aceitação atuais não substituem integralmente testes ponta a ponta da interface real.
4. **Segurança e autenticação:** o escopo inicial ainda não possui autenticação avançada, portanto esse aspecto não apresenta cobertura representativa.
5. **Desempenho e carga:** não há testes automatizados de carga ou desempenho documentados.
6. **Evolução do SAD:** funcionalidades futuras, como classificação ABC e tendências, ainda precisam de testes quando implementadas.
7. **Acompanhamento histórico da cobertura:** o percentual deve passar a ser registrado por iteração para permitir comparação.

## 7. Diagnóstico

O estado inicial é considerado **satisfatório como ponto de partida**, pois o projeto já possui testes automatizados em diferentes níveis. O principal desafio para o semestre é aumentar a confiança da suíte, cobrir lacunas, automatizar a execução no fluxo de integração e acompanhar quantitativamente a evolução da cobertura.

## 8. Meta para as iterações

A equipe deverá buscar:

- manter todos os testes existentes passando;
- adicionar testes para novas funcionalidades e correções;
- elevar progressivamente a cobertura do backend;
- evitar redução da cobertura sem justificativa;
- ampliar cenários de integração e aceitação;
- manter registro do resultado da suíte em cada iteração.
