# Relatório de Testes de Aceitação (QA) — Iteração 1

## 1. Identificação

- **Projeto:** Comercializa
- **Discente QA (Auditor):** Hildemberg Eling de Araújo Lucena ([@Hildemberg986](https://github.com/Hildemberg986))
- **Desenvolvedor Auditado:** Arthur José dos Santos Azevedo ([@arthurazvd](https://github.com/arthurazvd))
- **Iteração:** 1
- **User Story Auditada:** US14 — Ampliar testes automatizados dos modelos e regras de negócio
- **Issue da Disciplina:** [#601](https://github.com/tacianosilva/bsi-tasks/issues/601)

---

## 2. Contexto da Execução

Na Iteração 1, atuando como QA Engineer responsável pela auditoria cruzada da entrega do colega **Arthur Azevêdo**, foram executados e validados todos os cenários de aceitação especificados para a **US14**.

A **US14** teve como meta blindar o domínio e regras essenciais do sistema Comercializa contra regressões, garantindo que o faturamento de vendas nunca assuma valores negativos, que produtos em estoque crítico acionem recomendações explicáveis no SAD e que operações de venda reflitam deterministicamente nos indicadores gerenciais.

---

## 3. Cenários de Aceitação Auditados (BDD / Gherkin)

### CT-QA-US14-01 — Faturamento nunca deve ser negativo
```gherkin
Dado que existem vendas registradas no período
E o valor total dos descontos aplicados supera o valor bruto vendido
Quando o serviço de dashboard calcular a receita líquida
Então o faturamento resultante deve ser igual a R$ 0,00
E em hipótese alguma deve ser retornado um montante negativo
```
- **Resultado:** **PASSOU**
- **Evidência:** Teste automatizado `teste_receita_nao_pode_ser_negativa` em `backend/tests/test_services_unit.py`. Validação realizada com sucesso.

---

### CT-QA-US14-02 — Produto no estoque mínimo deve gerar recomendação de reposição
```gherkin
Dado que existe um produto cadastrado e ativo
E o saldo atual de estoque é exatamente igual ou inferior ao estoque mínimo configurado
Quando o SAD analisar os indicadores de estoque
Então o produto deve ser classificado com status de estoque crítico
E deve ser gerada uma recomendação explicável de reposição contendo ação e motivo
```
- **Resultado:** **PASSOU**
- **Evidência:** Testes `teste_reposicao_considera_estoque_minimo` e `teste_reposicao_sugere_pelo_menos_uma_unidade` em `backend/tests/test_services_unit.py`.

---

### CT-QA-US14-03 — Venda via API deve atualizar estoque e dashboard conjuntamente
```gherkin
Dado que existe um produto ativo com estoque positivo
Quando uma venda for efetuada via requisição POST para a API
Então a venda deve ser persistida com código HTTP 201
E o saldo do estoque do produto deve ser debitado
E a contagem de vendas e a receita do dashboard devem refletir a nova transação
```
- **Resultado:** **PASSOU**
- **Evidência:** Teste de integração `teste_venda_atualiza_estoque_e_dashboard` em `backend/tests/test_api.py`.

---

## 4. Avaliação de Mocks e SonarQube

- **Uso de Mock Objects:** Verificou-se a utilização de `unittest.mock.patch` isolando o cálculo de faturamento durante o teste do serviço de dashboard, garantindo independência de banco de dados.
- **Suíte de Testes:** Execução completa da suíte automatizada sem regressões.
- **SonarQube Quality Gate:**
  - Bugs: 0
  - Vulnerabilidades: 0
  - Security Hotspots: 0
  - Quality Gate: **PASSED**

---

## 5. Parecer Final do QA

A implementação da **US14** realizada por **Arthur Azevêdo** atende com excelência a todos os critérios de aceitação definidos para a Iteração 1. A suíte de testes de regras de negócio é determinística, possui tratamento adequado de limites e não introduziu regressões no projeto.

**Status da Auditoria:** **APROVADO**
