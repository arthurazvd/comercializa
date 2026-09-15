# Casos de Uso

## UC01 — Cadastrar produto

**Ator:** Comerciante  
**Pré-condição:** sistema disponível.  
**Fluxo principal:**
1. Usuário acessa Produtos.
2. Informa dados do produto.
3. Informa estoque e estoque mínimo.
4. Opcionalmente informa validade.
5. Confirma.
6. Sistema valida e salva.

## UC02 — Registrar venda

**Ator:** Comerciante  
**Pré-condição:** produto ativo e com estoque.  
**Fluxo principal:**
1. Usuário acessa Registrar venda.
2. Seleciona produto e quantidade.
3. Informa desconto, se houver.
4. Confirma a venda.
5. Sistema valida estoque.
6. Sistema registra venda.
7. Sistema reduz estoque.
8. Venda passa a alimentar as análises.

**Fluxo alternativo:** se a quantidade for superior ao estoque, a venda é recusada.

## UC03 — Consultar visão gerencial

**Ator:** Comerciante  
**Fluxo principal:**
1. Usuário abre o dashboard.
2. Sistema analisa dados recentes.
3. Sistema apresenta faturamento, vendas e alertas.
4. Sistema apresenta ranking.
5. Sistema apresenta recomendações priorizadas.

## UC04 — Avaliar reposição

1. SAD identifica estoque crítico.
2. SAD consulta movimentação recente.
3. SAD calcula sugestão inicial de reposição.
4. SAD atribui prioridade.
5. Usuário avalia a recomendação e decide se realizará a compra.

## UC05 — Avaliar produto próximo do vencimento

1. SAD encontra produto dentro da janela de validade.
2. SAD verifica estoque e movimentação.
3. SAD gera alerta.
4. SAD sugere avaliação de promoção/desconto.
5. Comerciante decide a ação.
