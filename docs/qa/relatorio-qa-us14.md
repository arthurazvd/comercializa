# Relatório de Testes de Aceitação --- US14

## 1. Identificação

**Projeto:** Comercializa\
**User Story:** US14 --- Ampliar testes automatizados dos modelos e
regras de negócio\
**Iteração:** 1\
**Responsável:** Arthur Azevêdo\
**Issue da disciplina:** #477

## 2. Contexto da execução

A atividade prevê a atuação como QA Engineer sobre a implementação de
outro integrante da equipe.

O projeto Comercializa é desenvolvido individualmente por Arthur
Azevêdo. Dessa forma, não existe outro integrante no G3 para a
realização do QA cruzado.

Para manter a validação prevista na atividade, os cenários de aceitação
definidos para a US14 foram executados sobre a implementação da própria
User Story, com os resultados documentados neste relatório.

## 3. Cenários de aceitação executados

### CT-A01 --- Faturamento nunca deve ser negativo

**Cenário BDD:**

``` gherkin
Dado que existem vendas no período analisado
E o valor total dos descontos é superior ao valor bruto vendido
Quando o dashboard calcular o faturamento
Então o faturamento apresentado deve ser igual a zero
E nunca deve ser apresentado um valor negativo
```

**Resultado:** PASSOU

**Evidência:** teste automatizado `teste_receita_nao_pode_ser_negativa`,
presente em `backend/tests/test_services_unit.py`.

------------------------------------------------------------------------

### CT-A02 --- Produto no estoque mínimo deve gerar recomendação de reposição

**Cenário BDD:**

``` gherkin
Dado que existe um produto ativo
E seu estoque atual é igual ou inferior ao estoque mínimo configurado
Quando o dashboard analisar a situação do estoque
Então o produto deve ser classificado como estoque crítico
E deve existir uma recomendação de reposição para o produto
```

**Resultado:** PASSOU

**Evidências:** testes automatizados das regras de reposição em
`backend/tests/test_services_unit.py` e testes do módulo SAD.

------------------------------------------------------------------------

### CT-A03 --- Venda deve atualizar estoque e dashboard

**Cenário BDD:**

``` gherkin
Dado que existe um produto ativo com estoque disponível
Quando uma venda desse produto for registrada pela API
Então a venda deve ser persistida
E o estoque do produto deve ser reduzido
E a quantidade de vendas apresentada no dashboard deve aumentar
E o faturamento do dashboard deve considerar a nova venda
```

**Resultado:** PASSOU

**Evidência:** teste de integração
`teste_venda_atualiza_estoque_e_dashboard`, presente em
`backend/tests/test_api.py`.

O teste valida conjuntamente:

1.  criação da venda através da API;
2.  persistência da operação;
3.  atualização do estoque;
4.  atualização da quantidade de vendas;
5.  atualização do faturamento no dashboard.

## 4. Testes unitários e Mock Objects

Foram adicionados testes unitários específicos para as regras de cálculo
de faturamento e sugestão de reposição.

Também foi utilizado Mock Object por meio de `unittest.mock.patch` para
isolar a função de cálculo de faturamento durante o teste do serviço de
dashboard.

O teste verifica tanto o valor retornado quanto a interação com a
dependência mockada.

## 5. Teste de integração

Foi implementado um teste de integração cobrindo o fluxo:

**API de vendas → persistência → atualização de estoque → serviço de
dashboard → resposta da API**

O cenário foi executado com sucesso.

## 6. Resultado da suíte

Após a implementação dos novos testes, a suíte automatizada foi
executada integralmente.

**Resultado:** 77 testes aprovados, sem regressões.

A cobertura foi medida utilizando `pytest-cov`, com geração do arquivo
`coverage.xml` para integração com o SonarQube.

## 7. Bugs encontrados

Não foram identificados bugs funcionais durante a execução dos cenários
de aceitação da US14.

## 8. Melhorias e observações

A extração das regras de cálculo de faturamento e reposição para funções
específicas tornou essas regras mais simples de testar isoladamente.

Como melhoria futura, outras regras atualmente concentradas no serviço
de dashboard também podem ser extraídas para funções menores e testáveis
de forma independente.

## 9. Conclusão

Os cenários de aceitação definidos para a US14 foram executados com
sucesso.

Os testes unitários, o uso de Mock Objects e o teste de integração
ampliaram a verificação automatizada das regras de negócio sem
introduzir regressões conhecidas no sistema.

A impossibilidade de realização do QA cruzado decorre da composição
individual do G3 e está registrada neste relatório.
