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

## 6. Especificação detalhada — US15 (Iteração 1)

### US15 — Ampliar testes de API e integração com Mock Objects e persistência

**Como** desenvolvedor da equipe do Comercializa,  
**quero** ampliar a suíte de testes automatizados de API e integração dos fluxos essenciais de produtos, categorias e vendas,  
**para** garantir códigos HTTP adequados, validações consistentes, isolamento de dependências via Mock Objects e integridade da persistência.

### Critérios de aceitação

1. O endpoint de produtos (`/api/products/`) deve possuir testes de integração cobrindo criação, listagem, consulta por ID e validação de schema.
2. A suíte deve isolar componentes de negócio e persistência utilizando Mock Objects (`unittest.mock.patch`, `MagicMock`) em testes de unidade de serializadores e viewsets.
3. Cenários de erro e exceção (criação com payload inválido, tentativa de excluir produto vinculado a vendas) devem retornar HTTP 400 com payload explicativo.
4. Testes de integração devem verificar a integridade transacional real no banco de dados e os códigos HTTP (200, 201, 400, 404).
5. A suíte deve executar com sucesso sem regressões e atender aos critérios do Quality Gate do SonarQube.

### Cenários de aceitação — BDD / Gherkin

#### Cenário 1 — Criação de produto com payload válido via API
```gherkin
Dado que existe uma categoria válida cadastrada no sistema
Quando o cliente enviar uma requisição POST para "/api/products/" com dados válidos de produto
Então a API deve responder com código HTTP 201 Created
E o produto retornado deve conter o ID gerado, SKU, nome, preços e saldo de estoque
E o registro deve estar efetivamente persistido no banco de dados
```

#### Cenário 2 — Rejeição de produto com payload incompleto ou inválido
```gherkin
Dado que a API de produtos está disponível
Quando o cliente enviar uma requisição POST para "/api/products/" sem o campo obrigatório "sale_price"
Então a API deve retornar código HTTP 400 Bad Request
E o corpo da resposta deve conter mensagem de validação sobre o campo faltante
E nenhum produto deve ser persistido no banco de dados
```

#### Cenário 3 — Bloqueio de exclusão de produto com vendas vinculadas
```gherkin
Dado que existe um produto previamente cadastrado
E que já foi registrada uma venda associada a este produto
Quando o cliente enviar uma requisição DELETE para "/api/products/{id}/"
Então a operação deve ser rejeitada com código HTTP 409 Conflict
E a mensagem deve informar que o produto possui histórico de vendas ou estoque
E o produto deve permanecer ativo no banco de dados
```

#### Cenário 4 — Isolamento de serviços externos via Mock Objects
```gherkin
Dado que o endpoint de dashboard ou relatórios integra múltiplos serviços analíticos
Quando a suíte unitária executar a validação de formatação de resposta
Então os cálculos de faturamento e recomendações devem ser interceptados por Mock Objects
E o comportamento da view deve ser verificado independentemente do estado do banco de dados
```

