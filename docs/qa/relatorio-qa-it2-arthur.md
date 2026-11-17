# Relatório de Testes de Aceitação (QA) — Iteração 2

## 1. Identificação

- **Projeto:** Comercializa
- **Discente QA (Auditor):** Hildemberg
- **Desenvolvedor Auditado:** Arthur Azevêdo
- **Iteração:** 2
- **User Story Auditada:** US04 — Atualização automática de estoque após venda e integridade transacional
- **Issue da Disciplina:** #480

---

## 2. Contexto da Execução

Em conformidade com as diretrizes da atividade **T03 (Implementação do User Story da Iteração 2 e Atuação como QA)**, foi realizada a auditoria cruzada de aceitação da funcionalidade implementada pelo colega **Arthur Azevêdo** na Iteração 2.

A **US04** estabelece que o estoque de produtos comercializados deve ser atualizado de forma estrita e transacional a cada venda concluída, garantindo:
1. Impossibilidade de ocorrência de estoque negativo;
2. Baixa atômica e consistente em vendas com múltiplos itens;
3. Restauração integral dos estoques e lotes específicos em caso de cancelamento/estorno de venda;
4. Proteção contra operações duplicadas por concorrência ou timeouts (idempotência).

---

## 3. Cenários de Aceitação Auditados (BDD / Gherkin)

### CT-QA-01 — Baixa regular de estoque após venda
```gherkin
Dado que existe um produto ativo com 10 unidades em estoque
Quando for registrada uma venda de 3 unidades do produto
Então a venda deve ser persistida com sucesso (HTTP 201)
E o estoque final do produto na base de dados deve ser exatamente 7 unidades
E deve ser gerada uma movimentação de estoque correspondente
```
- **Resultado:** **PASSOU**
- **Evidência:** Execução com sucesso do teste automatizado `teste_venda_reduz_estoque` em `backend/tests/test_api.py`.

---

### CT-QA-02 — Bloqueio de venda com quantidade superior ao estoque disponível
```gherkin
Dado que existe um produto com estoque igual a 2 unidades
Quando uma requisição de venda solicitar 5 unidades desse produto
Então a operação deve ser rejeitada com erro de validação (HTTP 400)
E o saldo em estoque do produto deve permanecer inalterado em 2 unidades
E nenhuma venda ou item de venda deve ser persistido
```
- **Resultado:** **PASSOU**
- **Evidência:** Execução do teste `teste_venda_rejeita_estoque_insuficiente` em `backend/tests/test_api.py` e `teste_sem_estoque_negativo_venda` em `backend/tests/test_acceptance.py`.

---

### CT-QA-03 — Venda atômica com múltiplos itens e controle por lote
```gherkin
Dado que existem dois produtos ativos no catálogo:
  | Produto | Estoque Inicial | Lotes Configurados |
  | Item A  | 10              | Lote único         |
  | Item B  | 5               | Múltiplos lotes    |
Quando for submetida uma única venda contendo 4 unidades do Item A e 2 unidades do Item B
Então todos os itens devem ser debitados em uma única transação atômica
E os saldos finais devem ser 6 e 3 unidades, respectivamente
E caso haja erro em qualquer um dos itens, toda a operação deve sofrer rollback
```
- **Resultado:** **PASSOU**
- **Evidência:** Execução de `teste_venda_multiple_items` em `backend/tests/test_api.py` e `teste_estoque_atualizado_mesma_transacao` em `backend/tests/test_acceptance.py`.

---

### CT-QA-04 — Estorno e recomposição de estoque e lotes
```gherkin
Dado que uma venda contendo múltiplos lotes foi registrada
Quando o operador solicitar o estorno dessa venda com justificativa válida
Então a venda deve ser marcada como cancelada
E as quantidades exatas baixadas de cada lote devem ser devolvidas aos lotes originais
E o saldo total do produto deve ser recomposto
```
- **Resultado:** **PASSOU**
- **Evidência:** Execução da suíte completa de `backend/tests/test_sale_reversal.py` (`test_reversal_restores_stock_and_creates_movement`, `test_reversal_restores_original_purchase_cost`).

---

### CT-QA-05 — Idempotência e prevenção de duplicidade
```gherkin
Dado que um payload de venda é enviado com cabeçalho de idempotência
Quando a mesma requisição for reenviada (ex: após timeout de rede)
Então o sistema deve reconhecer a chave idempotente
E não deve duplicar a venda nem debitar novamente o estoque do produto
```
- **Resultado:** **PASSOU**
- **Evidência:** Execução dos testes em `backend/tests/test_idempotency.py`.

---

## 4. Avaliação de Qualidade e SonarQube

- **Execução dos Testes Automatizados:** 181 testes executados, 100% de aprovação (0 falhas, 0 erros).
- **Cobertura de Código Backend:** 94% de cobertura de declarações no módulo `backend/core/` (requisito mínimo: >= 70%).
- **SonarQube Quality Gate:**
  - **Bugs:** 0
  - **Vulnerabilities:** 0
  - **Security Hotspots:** 0
  - **Code Smells:** 0 impeditivos
  - **Duplicações:** < 3%
  - **Quality Gate:** **PASSED**

---

## 5. Conclusão e Parecer do QA

A implementação da **US04** pelo colega **Arthur Azevêdo** atende integralmente a todos os critérios de aceitação estipulados para a Iteração 2. O tratamento transacional é robusto, com garantias de atomicidade no banco de dados e controle rigoroso de lotes e estoque não negativo.

Recomenda-se a aprovação e integração do Pull Request na branch principal (`develop` / `main`).

**Status da Auditoria:** **APROVADO**
