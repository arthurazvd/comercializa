# Product Backlog — User Stories

## 1. Objetivo

Este documento apresenta o Product Backlog do **Comercializa**, organizado em histórias de usuário que orientam a evolução do sistema durante a disciplina de Teste de Software.

## 2. Perfis considerados

- **Comerciante:** proprietário ou responsável pelo pequeno comércio que utiliza o sistema no dia a dia.
- **Gestor:** usuário interessado nos indicadores, alertas e recomendações do módulo de apoio à decisão.
- **Equipe de desenvolvimento:** responsável pela manutenção, evolução, qualidade e testes do sistema.

## 3. Histórias de usuário

| ID | História de usuário | Prioridade | Critérios de aceitação resumidos |
|---|---|---|---|
| US01 | Como comerciante, quero cadastrar e manter categorias para organizar os produtos do estabelecimento. | Alta | Permitir criar, listar, editar e remover categorias, respeitando as validações definidas. |
| US02 | Como comerciante, quero cadastrar e manter produtos para controlar os itens comercializados. | Alta | Permitir CRUD de produtos com preços, estoque, estoque mínimo, categoria, validade e situação. |
| US03 | Como comerciante, quero registrar vendas com um ou mais itens para manter o histórico comercial atualizado. | Alta | Registrar venda, itens, quantidades, preços e desconto, calculando subtotal e total corretamente. |
| US04 | Como comerciante, quero que o estoque seja atualizado automaticamente após uma venda para evitar divergências. | Alta | Reduzir estoque após venda e impedir operação que resulte em estoque negativo. |
| US05 | Como gestor, quero visualizar um dashboard com indicadores do negócio para acompanhar rapidamente a situação do comércio. | Alta | Exibir faturamento, quantidade de vendas, rankings, alertas e indicadores relevantes. |
| US06 | Como gestor, quero identificar produtos com estoque crítico para priorizar a reposição. | Alta | Listar produtos cujo estoque esteja igual ou abaixo do mínimo e apresentar justificativa. |
| US07 | Como gestor, quero visualizar os produtos mais vendidos para entender a demanda. | Média | Apresentar ranking calculado a partir dos itens vendidos em período analisado. |
| US08 | Como gestor, quero identificar produtos com baixa movimentação para avaliar ações comerciais. | Média | Identificar produtos sem vendas ou com baixa saída no período configurado. |
| US09 | Como gestor, quero receber alertas de produtos próximos do vencimento para reduzir perdas. | Alta | Identificar produtos dentro da janela de vencimento e apresentar o motivo do alerta. |
| US10 | Como gestor, quero receber recomendações de reposição para melhorar as decisões de compra. | Alta | Considerar estoque atual, mínimo e movimentação, exibindo ação e justificativa. |
| US11 | Como gestor, quero receber recomendações promocionais para produtos com baixa saída ou risco de vencimento. | Média | Sugerir avaliação de promoção quando as regras do SAD forem satisfeitas. |
| US12 | Como gestor, quero analisar produtos por participação no faturamento para identificar itens mais relevantes. | Média | Implementar classificação ABC ou mecanismo equivalente com resultado verificável. |
| US13 | Como gestor, quero comparar períodos de vendas para identificar tendências de crescimento ou queda. | Média | Permitir comparação entre períodos e apresentar a variação de forma compreensível. |
| US14 | Como equipe de desenvolvimento, quero ampliar os testes automatizados dos modelos e regras de negócio para reduzir regressões. | Alta | Testar caminhos principais, limites e erros das regras de domínio. |
| US15 | Como equipe de desenvolvimento, quero ampliar os testes de API e integração para garantir o funcionamento conjunto dos componentes. | Alta | Cobrir endpoints principais, códigos HTTP, persistência e regras integradas. |
| US16 | Como equipe de desenvolvimento, quero manter testes de aceitação para validar os principais fluxos sob a perspectiva do usuário. | Alta | Automatizar cenários representativos de cadastro, venda e uso do SAD. |
| US17 | Como equipe de desenvolvimento, quero acompanhar a cobertura de testes para identificar trechos sem verificação automatizada. | Alta | Gerar relatório de cobertura reproduzível e registrar a evolução ao longo das iterações. |
| US18 | Como equipe de desenvolvimento, quero executar os testes automaticamente no CI para detectar regressões a cada alteração. | Alta | Workflow deve instalar dependências, executar testes e falhar quando a suíte falhar. |

## 4. Especificação detalhada — US14

### US14 — Ampliar testes automatizados dos modelos e regras de negócio

**Como** integrante da equipe de desenvolvimento,  
**quero** ampliar os testes automatizados das regras de negócio do Comercializa,  
**para** reduzir o risco de regressões nas funcionalidades relacionadas ao estoque, faturamento e recomendações do sistema.

### Critérios de aceitação

- As principais regras de negócio do serviço de dashboard devem possuir testes automatizados.
- Os testes unitários devem isolar dependências externas utilizando Mock Objects quando aplicável.
- Devem existir cenários de limite para estoque e faturamento.
- Pelo menos um teste de integração deve validar o comportamento conjunto entre API, persistência e regra de negócio.
- A suíte existente deve continuar passando após a inclusão dos novos testes.
- A cobertura deve ser gerada por meio do `pytest-cov`.

### Cenários de aceitação — BDD/Gherkin

#### Cenário 1 — Faturamento nunca deve ser negativo

```gherkin
Dado que existem vendas no período analisado
E o valor total dos descontos é superior ao valor bruto vendido
Quando o dashboard calcular o faturamento
Então o faturamento apresentado deve ser igual a zero
E nunca deve ser apresentado um valor negativo

### Cenário 2 — Produto no estoque mínimo deve ser considerado crítico

```gherkin
Dado que existe um produto ativo
E seu estoque atual é igual ao estoque mínimo configurado
Quando o dashboard analisar a situação do estoque
Então o produto deve ser classificado como estoque crítico
E deve existir uma recomendação de reposição para o produto

### Cenário 3 — Venda deve refletir nos indicadores do dashboard

```gherkin
Dado que existe um produto ativo com estoque disponível
Quando uma venda desse produto for registrada pela API
Então a venda deve ser persistida
E o estoque do produto deve ser reduzido
E a quantidade de vendas apresentada no dashboard deve aumentar
E o faturamento do dashboard deve considerar a nova venda

## 5. Definition of Done

Uma User Story é considerada concluída quando:

1. seus critérios de aceitação forem atendidos;
2. o código estiver integrado ao repositório do projeto;
3. os testes automatizados relacionados estiverem implementados ou atualizados;
4. a suíte de testes relevante estiver passando;
5. a documentação afetada estiver atualizada;
6. não houver regressão conhecida introduzida pela alteração.

---

## 6. Especificação detalhada — US09 (Iteração 2)

### US09 — Alertas inteligentes de produtos próximos do vencimento e análise de risco financeiro

**Como** gestor do comércio,  
**quero** receber alertas categorizados de produtos próximos do vencimento com o cálculo do valor financeiro em risco,  
**para** priorizar promoções, antecipar perdas e tomar decisões rápidas de gestão de estoque.

### Critérios de aceitação

1. O sistema deve analisar lotes cadastrados (`StockLot`) e saldos legados do produto (`Product`) com data de validade ativa.
2. Cada alerta deve ser classificado em faixas de severidade:
   - `Vencido` (< 0 dias): itens já expirados.
   - `Crítico` (0 a 7 dias): risco iminente de descarte.
   - `Alerta` (8 a 15 dias): janela prioritária para liquidação ou promoção.
   - `Atenção` (16 a 30 dias): monitoramento para evitar perda futura.
3. O sistema deve calcular o montante financeiro em risco (`capital_em_risco = quantidade × custo_unitario`) e a receita potencial associada.
4. Deve existir um endpoint REST dedicado (`/api/alerts/expiration/`) permitindo filtrar por janela de dias (`window_days`) e severidade (`severity`).
5. Produtos não perecíveis, sem validade cadastrada ou com saldo zerado não devem gerar alertas espúrios.
6. A funcionalidade deve ter testes unitários para valores-limite de datas e testes de integração de API.

### Cenários de aceitação — BDD / Gherkin

#### Cenário 1 — Classificação de alerta crítico com risco financeiro calculado
```gherkin
Dado que existe um produto perecível com lote de 10 unidades com custo unitário de R$ 5,00
E a data de validade desse lote é de 3 dias a partir de hoje
Quando o gestor consultar os alertas de vencimento do sistema
Então o lote deve ser retornado com severidade "critico"
E o capital em risco calculado deve ser de R$ 50,00
E deve ser sugerida a ação de "Liquidação urgente com desconto de até 50% ou degustação/queima imediata"
```

#### Cenário 2 — Produto com múltiplos lotes em severidades distintas
```gherkin
Dado que existe um produto perecível com dois lotes:
  | Lote | Quantidade | Validade        | Custo Unitário |
  | A    | 5          | Hoje + 5 dias   | R$ 10,00       |
  | B    | 20         | Hoje + 25 dias  | R$ 10,00       |
Quando o gestor consultar os alertas de vencimento para uma janela de 30 dias
Então o Lote A deve ser classificado como severidade "critico"
E o Lote B deve ser classificado como severidade "atencao"
E o resumo financeiro deve totalizar R$ 250,00 de capital em risco acumulado
```

#### Cenário 3 — Identificação e segregação de lotes já vencidos
```gherkin
Dado que existe um produto perecível com lote com validade expirada há 2 dias
Quando o gestor consultar os alertas de vencimento
Então o lote deve ser classificado como severidade "vencido"
E deve apresentar recomendação para segregar e descartar o item do estoque comercializável
```

#### Cenário 4 — Consulta de alertas via API com filtro de janela temporal
```gherkin
Dado que a API de alertas de vencimento está disponível
Quando o cliente enviar uma requisição GET para "/api/alerts/expiration/?window_days=7"
Então a resposta deve ter código HTTP 200
E a lista deve conter apenas lotes cuja validade ocorra dentro dos próximos 7 dias ou que já estejam vencidos
E não devem ser exibidos lotes com validade superior a 7 dias
```

