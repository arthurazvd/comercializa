# Módulo de Apoio à Decisão

## Objetivo

O SAD deve ir além de mostrar dados. Ele deve ajudar o comerciante a responder:

- O que preciso repor primeiro?
- O que está vendendo mais?
- O que está parado?
- O que pode vencer?
- Onde existe risco de perder venda por falta de estoque?
- Que produto pode entrar em promoção?
- Quais produtos têm maior impacto no negócio?

## Dados utilizados

- estoque atual;
- estoque mínimo;
- quantidade vendida;
- data e horário das vendas;
- preço de venda;
- preço de compra;
- validade;
- histórico por produto.

## Regras implementadas no protótipo

### 1. Estoque crítico

```text
se estoque_atual <= estoque_minimo:
    gerar alerta de reposição
```

### 2. Velocidade de venda

```text
velocidade = unidades_vendidas_nos_ultimos_30_dias / 30
```

Esse indicador permite diferenciar dois produtos que possuem o mesmo estoque, mas ritmos de venda diferentes.

### 3. Cobertura aproximada

```text
dias_de_cobertura = estoque_atual / velocidade_de_venda
```

Quanto menor a cobertura, maior tende a ser a urgência de reposição.

### 4. Sugestão inicial de reposição

O protótipo considera estoque mínimo e velocidade recente. A fórmula ainda é deliberadamente simples e deverá ser calibrada com dados reais.

### 5. Risco de vencimento

Produtos que vencem nos próximos 15 dias geram alerta. Produtos com prazo ainda menor recebem maior prioridade.

### 6. Baixa movimentação

Produtos com estoque positivo e nenhuma venda nos últimos 30 dias são destacados para análise.

### 7. Recomendações explicáveis

Cada recomendação possui:
- tipo;
- prioridade;
- produto;
- ação sugerida;
- justificativa.

## Próximas análises

### Classificação ABC

Classificar produtos pela participação no faturamento:
- A: maior impacto;
- B: impacto intermediário;
- C: menor impacto.

### Tendência de vendas

Comparar períodos para detectar crescimento ou queda.

### Previsão de demanda

Após existir histórico suficiente, estimar vendas futuras e sugerir compras antecipadamente.

### Sazonalidade

Detectar produtos que vendem mais em determinados dias, meses ou épocas.

### Margem e rentabilidade

Cruzar volume vendido com margem para evitar que o ranking considere somente quantidade.

## Princípio importante

O SAD não deve tomar automaticamente decisões comerciais irreversíveis. Ele fornece evidências e recomendações para que o comerciante decida.
