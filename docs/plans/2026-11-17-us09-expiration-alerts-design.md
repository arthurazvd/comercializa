# Design Doc — US09: Alertas Inteligentes de Vencimento e Análise de Risco Financeiro

**Data:** 17/11/2026  
**Autor:** Hildemberg (hildemberg986)  
**Contexto:** Tarefa T03 — Iteração 2 (Engenharia de Software e Garantia de Qualidade)  
**Status:** Aprovado  

---

## 1. Contexto e Motivação

No varejo de pequenos e médios estabelecimentos, perdas por validade expirada representam um impacto direto no faturamento e na margem líquida. O sistema *Comercializa* possui registro de datas de validade tanto a nível de cadastro legado de produto (`Product.expiration_date`) quanto a nível de rastreamento por lotes físicos (`StockLot.expiration_date`), suportando custos unitários de aquisição distintos.

Atualmente, o SAD (Sistema de Apoio à Decisão) contava apenas com uma verificação simplificada embutida no cálculo geral do dashboard, com janela fixa de 15 dias e sem quantificação financeira de perdas potenciais.

A **US09** expande essa capacidade para um **Motor Analítico de Risco de Vencimento** e uma **API dedicada**, fornecendo:
1. Classificação em 4 faixas de severidade (`VENCIDO`, `CRÍTICO`, `ALERTA` e `ATENÇÃO`).
2. Quantificação do **capital em risco** (custo de reposição e receita potencial).
3. Recomendações explicáveis e orientadas à ação para o gestor comercial.
4. Filtros customizáveis de janela temporal e severidade.

---

## 2. Arquitetura e Componentes

### 2.1 Módulo de Serviço: `backend/core/expiration_service.py`
Funções puras e de serviço para processamento analítico:
- `classify_expiration(days_remaining, window_days)`: Classifica a faixa de severidade com base em análise de valores-limite.
- `calculate_lot_risk(lot_or_product, days_remaining)`: Calcula `cost_at_risk` e `potential_revenue_loss`.
- `get_expiration_alerts(reference_date=None, window_days=30, severity=None, category_id=None)`:
  - Coleta lotes ativos (`quantity > 0`) com data de validade preenchida.
  - Trata o saldo legado do produto caso não haja lote discriminado.
  - Agrupa métricas de resumo (`total_items_at_risk`, `total_cost_at_risk`, `total_revenue_loss`, contagem por severidade).
  - Retorna estrutura serializável.

### 2.2 Faixas de Severidade e Regras de Negócio

| Faixa | Intervalo (dias restantes) | Ação Recomendada |
|---|---|---|
| **VENCIDO** | `days < 0` | Segregar e descartar/baixar do estoque; produto impróprio para consumo. |
| **CRÍTICO** | `0 <= days <= 7` | Ação imediata: queima de estoque ou desconto agressivo (até 50%). |
| **ALERTA** | `8 <= days <= 15` | Ação tática: promoção moderada (20%) e destaque na gôndola. |
| **ATENÇÃO** | `16 <= days <= window_days` (padrão 30) | Monitoramento e priorização de saída no PDV (FIFO). |

### 2.3 Endpoint REST: `GET /api/alerts/expiration/`
- Parâmetros aceitos na query string:
  - `window_days`: inteiro (1 a 365, default 30).
  - `severity`: string opcional (`vencido`, `critico`, `alerta`, `atencao`).
  - `category_id`: inteiro opcional.
- Resposta JSON 200 OK com `summary` e `alerts`.
- Retorna 400 Bad Request em parâmetros inválidos (ex: janela não numérica ou <= 0).

---

## 3. Estratégia de Testes

1. **Testes Unitários (`backend/tests/test_expiration_alerts.py`):**
   - Cobertura de partições de equivalência e limites temporais (-1, 0, 7, 8, 15, 16, 30, 31 dias).
   - Validação dos cálculos financeiros de risco.
   - Isolamento de data/hora atual utilizando mock (`unittest.mock.patch('django.utils.timezone.now')`).
   - Produtos não perecíveis ou sem validade não devem emitir falsos positivos.

2. **Testes de Integração:**
   - Requisições reais via `APIClient` do Django REST Framework para o endpoint `/api/alerts/expiration/`.
   - Criação de produtos e lotes no banco de teste e verificação da resposta estruturada.
   - Filtros de query string e tratamento de erro 400.

---

## 4. Auditoria Cruzada de QA (Colega Arthur Azevêdo)

- Criação do relatório formal `docs/qa/relatorio-qa-us04-arthur.md`.
- Execução e verificação dos testes de aceitação da Iteração 2 (US04 - Integridade do estoque e estorno nas vendas).
- Registro de evidências, logs de execução do pytest e conformidade com o Quality Gate do SonarQube.
