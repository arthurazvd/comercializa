# Modelo de Dados

## Entidades iniciais

### Category
- id
- name

### Product
- id
- name
- category
- sku
- purchase_price
- sale_price
- stock
- minimum_stock
- expiration_date
- active
- created_at

### Sale
- id
- created_at
- discount

### SaleItem
- id
- sale
- product
- quantity
- unit_price

## Relacionamentos

```text
Category 1 ───── N Product
Product  1 ───── N SaleItem
Sale     1 ───── N SaleItem
```

O preço unitário é armazenado em `SaleItem` para manter o histórico correto mesmo quando o preço atual do produto mudar.

## Evoluções previstas

- Supplier;
- Purchase;
- PurchaseItem;
- StockMovement;
- Promotion;
- Recommendation;
- DecisionFeedback.

`DecisionFeedback` poderá registrar se o comerciante aceitou ou ignorou uma recomendação, permitindo avaliar a utilidade do SAD.

## Atualização 29/10/2026 — StockMovement

`StockMovement` adiciona auditoria de mudanças de saldo:

| Campo | Tipo / regra |
| --- | --- |
| `product` | FK para Product, com `PROTECT` |
| `sale` | FK opcional para Sale, com `PROTECT` |
| `delta` | inteiro assinado, positivo na entrada e negativo na saída |
| `stock_before` / `stock_after` | inteiros não negativos |
| `reason` | `sale` ou `adjustment` |
| `note` | justificativa, até 255 caracteres |
| `created_at` | instante da operação |

O lançamento de venda e seus movimentos ocorre atomicamente. A alteração de saldo pelo cadastro também gera um lançamento de ajuste. O saldo de abertura de produtos antigos não tem histórico retroativo.

## Modelo em produção (extensões V1.2.0)

`Product`: adiciona `perishable`, `image_updated_at` (nulo = sem foto); estoque mínimo, validade legada e SKU opcional. `ProductImage`: `id`, `product_id UNIQUE (ON DELETE CASCADE)`, `filename` (SKU/ID + `.jpg`), `data BYTEA`, `size`, `updated_at`. Cardinalidade Product 1 → 0..1 ProductImage; a foto não é duplicada nas linhas de vendas.

`Sale`: `discount`, `canceled_at`, `cancellation_reason`, `canceled_by`. `SaleItem`: snapshot de quantidade e preço na data da venda. `StockMovement`: `reason` (`sale`/`reversal`/`adjustment`), `justification`, `stock_before`, `stock_after`, `note`; `StockLot`: quantidade por lote/validade; `StockLotAllocation`: vínculo de saída/devolução a lote. `IdempotencyRecord`: chave e resposta original de operações POST para tolerar reenvios.

**Migração:** `backend/core/migrations/0007_product_image.py` adiciona `image_updated_at` e tabela `ProductImage`; não altera nem exclui vendas ou estoques anteriores. A exclusão de produto sem dependências elimina sua imagem por CASCADE. Trocar SKU de produto com foto atualiza o nome lógico no registro (os bytes permanecem os mesmos).

**Invariantes:** imagem JPEG válida até 102400 bytes, até 4096 pixels em cada dimensão na validação do servidor; frontend padroniza 800×800 px ou menor. Dados binários não podem constar em `/api/products/`. Excluir a imagem define `image_updated_at=NULL`.

## Atualização V1.3.0 — custo por lote

`StockLot.unit_cost` registra custo histórico por lote mesmo para itens sem validade (`expiration_date = NULL`). `StockMovement.unit_cost` registra o preço informado no recebimento. `SaleItem.cost_total` congela o custo total da linha da venda (nulo para vendas anteriores sem histórico). `Product.purchase_price` torna-se referência de custo para novas operações; `Product.sale_price` continua representando o preço de venda vigente.

Migração `0008_cost_by_lot`: lotes já cadastrados recebem o custo de referência conhecido, não um histórico reconstruído; a compra original não está disponível para inferência. Consulta `GET /api/products/{id}/lots/`. Regras detalhadas em [UC13–15](24-custos-por-lote-e-previsualizacao-de-estoque.md).

## Extensão V1.4.0 — FinancialEntry

A migração `0009_financial_entries` introduz `FinancialEntry` para despesas (`expense`) e investimentos em ativos (`investment`), com `category`, `description`, `amount`, `entry_date`, `created_at`, `created_by`, `voided_at` e `voided_by`. Os custos dos produtos vendidos já estão congelados em `SaleItem.cost_total` desde a V1.3.0; custo por compra fica em `StockLot.unit_cost` / `StockMovement.unit_cost`. Ver [gestão financeira](25-gestao-financeira.md).
