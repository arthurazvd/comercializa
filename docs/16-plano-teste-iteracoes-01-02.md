# Plano de Teste das Iterações 1 e 2 (PTI)

## 1. Identificação

**Projeto:** Comercializa  
**Responsável:** Arthur Azevêdo  
**Unidade:** I  
**Iterações:** 1 e 2

## 2. Objetivo

Este documento detalha os casos de teste planejados para as User Stories priorizadas nas duas primeiras iterações. Os casos cobrem unidade, integração/API e aceitação, com foco inicial na ampliação da suíte e, em seguida, na automação contínua e integridade do fluxo de venda/estoque.

## 3. Iteração 1

**User Stories:** US14, US15 e US17.  
**Objetivo:** ampliar testes de domínio e API e consolidar a medição de cobertura.

### CT-I1-01 — Cálculo do total de uma venda

**User Story:** US14  
**Nível:** Unidade  
**Pré-condições:** produtos válidos disponíveis; ambiente Django de teste inicializado.  
**Dados de entrada:** itens com quantidades e preços conhecidos e desconto válido.

**Passos:**
1. Criar os produtos necessários.
2. Criar uma venda com os itens definidos.
3. Aplicar o desconto do cenário.
4. Calcular/consultar subtotal e total.

**Resultado esperado:** subtotal corresponde à soma de quantidade × preço dos itens e o total corresponde ao subtotal após aplicação correta do desconto.

### CT-I1-02 — Rejeição de operação que viola regra de estoque

**User Story:** US14  
**Nível:** Unidade  
**Pré-condições:** produto com estoque conhecido.  
**Dados de entrada:** quantidade solicitada superior ao estoque disponível.

**Passos:**
1. Criar produto com estoque limitado.
2. Tentar executar a operação de venda com quantidade superior à disponível.
3. Consultar o produto após a tentativa.

**Resultado esperado:** a operação inválida é rejeitada conforme a regra de negócio e o estoque não fica negativo.

### CT-I1-03 — Cadastro de produto válido via API

**User Story:** US15  
**Nível:** Integração/API  
**Pré-condições:** API disponível no ambiente de teste e categoria válida cadastrada.  
**Dados de entrada:** produto com nome, preço, estoque, estoque mínimo e categoria válidos.

**Passos:**
1. Enviar requisição de criação ao endpoint de produtos.
2. Verificar o código HTTP retornado.
3. Consultar o registro persistido.

**Resultado esperado:** API retorna sucesso de criação e o produto é persistido com os valores informados.

### CT-I1-04 — Rejeição de produto inválido via API

**User Story:** US15  
**Nível:** Integração/API  
**Pré-condições:** API disponível no ambiente de teste.  
**Dados de entrada:** payload incompleto ou com valor inválido para campo obrigatório.

**Passos:**
1. Enviar payload inválido ao endpoint de produtos.
2. Registrar código e corpo da resposta.
3. Consultar a base para verificar se houve persistência indevida.

**Resultado esperado:** API retorna erro de validação (4xx) e não persiste produto inválido.

### CT-I1-05 — Geração do relatório de cobertura

**User Story:** US17  
**Nível:** Qualidade/automação  
**Pré-condições:** dependências do backend instaladas e suíte disponível.  
**Dados de entrada:** suíte automatizada do repositório.

**Passos:**
1. Acessar `backend/`.
2. Executar `pytest --cov=core --cov-report=term-missing --cov-report=xml:coverage.xml`.
3. Aguardar o término da suíte.
4. Verificar a existência de `coverage.xml`.

**Resultado esperado:** suíte termina sem falhas e é produzido um XML válido com a cobertura medida.

### CT-I1-06 — Regressão do baseline existente

**User Story:** US14 / US15 / US17  
**Nível:** Regressão  
**Pré-condições:** ambiente configurado.  
**Dados de entrada:** conjunto completo de testes automatizados.

**Passos:**
1. Executar a suíte completa.
2. Comparar falhas com o baseline registrado.
3. Analisar eventual redução de cobertura.

**Resultado esperado:** testes previamente aprovados continuam passando; qualquer regressão é bloqueada e registrada antes da conclusão da iteração.

## 4. Iteração 2

**User Stories:** US16, US18 e US04.  
**Objetivo:** fortalecer fluxos de aceitação, automatizar a regressão no CI e garantir integridade do estoque após vendas.

### CT-I2-01 — Venda reduz estoque corretamente

**User Story:** US04  
**Nível:** Integração  
**Pré-condições:** produto cadastrado com estoque 10.  
**Dados de entrada:** venda de 3 unidades do produto.

**Passos:**
1. Criar produto com estoque igual a 10.
2. Registrar venda de 3 unidades.
3. Recarregar o produto da base.
4. Consultar o estoque final.

**Resultado esperado:** venda é registrada e estoque final é 7.

### CT-I2-02 — Venda com múltiplos itens atualiza todos os estoques

**User Story:** US04 / US16  
**Nível:** Aceitação/integração  
**Pré-condições:** dois produtos com estoques conhecidos.  
**Dados de entrada:** venda contendo quantidades válidas dos dois produtos.

**Passos:**
1. Criar os dois produtos.
2. Registrar uma única venda contendo ambos.
3. Consultar a venda e seus itens.
4. Consultar os estoques dos produtos.

**Resultado esperado:** venda e itens são persistidos, total é coerente e ambos os estoques são reduzidos exatamente pelas quantidades vendidas.

### CT-I2-03 — Fluxo de estoque crítico após venda

**User Story:** US16 / US04  
**Nível:** Aceitação  
**Pré-condições:** produto com estoque próximo do estoque mínimo.  
**Dados de entrada:** venda que faça o estoque atingir ou ultrapassar o limiar crítico.

**Passos:**
1. Criar produto com estoque e mínimo definidos.
2. Registrar a venda.
3. Consultar o indicador/serviço de estoque crítico.

**Resultado esperado:** produto passa a ser identificado corretamente como estoque crítico e a informação é coerente com o estoque persistido.

### CT-I2-04 — Workflow executa em push para main

**User Story:** US18  
**Nível:** CI  
**Pré-condições:** workflow versionado e Secrets configurados.  
**Dados de entrada:** `push` para `main`.

**Passos:**
1. Enviar alteração para `main`.
2. Abrir a execução correspondente no GitHub Actions.
3. Verificar instalação das dependências.
4. Verificar execução do pytest e geração de cobertura.
5. Verificar etapa do SonarQube.

**Resultado esperado:** workflow é disparado automaticamente, testes passam, `coverage.xml` é gerado e a análise é enviada ao SonarQube LABENS.

### CT-I2-05 — Workflow executa em Pull Request para main

**User Story:** US18  
**Nível:** CI  
**Pré-condições:** workflow versionado; branch de teste disponível.  
**Dados de entrada:** Pull Request cujo destino seja `main`.

**Passos:**
1. Abrir Pull Request para `main`.
2. Acompanhar a execução do workflow.
3. Verificar o resultado da suíte e cobertura.

**Resultado esperado:** workflow é iniciado automaticamente e impede uma validação bem-sucedida quando a suíte apresenta falhas.

### CT-I2-06 — Publicação das métricas no SonarQube

**User Story:** US18  
**Nível:** CI/qualidade  
**Pré-condições:** `SONAR_TOKEN` e `SONAR_HOST_URL` cadastrados em GitHub Secrets; projeto existente/autorizado no LABENS.  
**Dados de entrada:** código da branch analisada e `backend/coverage.xml`.

**Passos:**
1. Executar o workflow em contexto com acesso aos Secrets.
2. Confirmar conclusão da etapa de testes.
3. Confirmar execução do scanner.
4. Abrir o projeto no dashboard do SonarQube LABENS.

**Resultado esperado:** scanner finaliza com sucesso e o dashboard apresenta a análise do commit, incluindo a cobertura importada.

## 5. Matriz de rastreabilidade

| User Story | Casos de teste |
|---|---|
| US14 | CT-I1-01, CT-I1-02, CT-I1-06 |
| US15 | CT-I1-03, CT-I1-04, CT-I1-06 |
| US17 | CT-I1-05, CT-I1-06 |
| US04 | CT-I2-01, CT-I2-02, CT-I2-03 |
| US16 | CT-I2-02, CT-I2-03 |
| US18 | CT-I2-04, CT-I2-05, CT-I2-06 |

## 6. Critérios de conclusão

As iterações atendem ao plano de teste quando os casos aplicáveis estiverem executados, as falhas relevantes estiverem corrigidas ou formalmente registradas, a regressão estiver aprovada e as evidências de CI/cobertura estiverem disponíveis no repositório e no SonarQube.
