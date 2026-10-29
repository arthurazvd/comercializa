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
