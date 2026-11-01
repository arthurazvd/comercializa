# UC13–UC15 — Custos por lote e visualização de estoque (V1.3.0)

## Objetivo e limites

Permitir nova entrada de mercadoria a custo diferente **sem alterar o custo dos lotes anteriores**. O preço de venda é único por produto (preço vigente de tabela), enquanto o custo unitário fica registrado separadamente em cada lote. Isso **não** significa que os lotes antigos serão vendidos pelo preço antigo: novas vendas usam o preço atual, mas o custo de cada saída é registrado pelo lote consumido. A data da compra e o custo são auditáveis. Para produtos perecíveis, o sistema mantém a baixa FEFO (primeiro a vencer); para produtos sem validade, baixa por ordem de chegada.

### UC13 — Receber mercadoria com novo preço de compra

- **Ator:** operador autenticado.
- **Pré-condição:** produto existente e preço de venda acima do custo da nova entrada.
- **Fluxo:** Movimentações → selecionar produto → informar quantidade positiva, justificativa `Recebimento` e **custo unitário do lote** → informar validade somente se for perecível → escolher se atualiza o **custo de referência** da ficha → opcionalmente informar **novo preço de venda** → confirmar.
- **Pós-condições:** uma operação transacional cria `StockMovement` e `StockLot`, aumenta `Product.stock`, mantém o custo unitário histórico dos lotes anteriores, e altera `Product.purchase_price`/`Product.sale_price` somente quando solicitado. Uma mesma chave de idempotência não cria dois lotes.
- **Exceções:** preço de venda menor ou igual ao custo da nova entrada é recusado com indicação para corrigir o preço. Entrada de perecível sem validade também é recusada. A compra não altera retroativamente vendas anteriores.

### UC14 — Consultar foto e composição do estoque

- **Ator:** operador autenticado.
- **Fluxo:** Estoque → tocar/clicar no nome de um item → visualizar miniatura ampliada, SKU, preço de venda, unidades, custo médio do saldo e histórico dos lotes (preço pago, recebido, disponível e validade). A foto é consultada pelo endpoint autenticado já existente. A lista de lotes é carregada somente ao abrir a janela.
- **Fluxo alternativo:** um produto sem foto usa ícone padrão. Um produto sem lotes explícitos exibe seu saldo legado estimado a custo de referência. Se a API falhar, a janela continua utilizável e mostra erro local, sem pop-up de gravação.

### UC15 — Vender ou estornar com custo histórico

- Cada venda armazena `SaleItem.unit_price` (preço de venda praticado) e `SaleItem.cost_total` (soma dos custos dos lotes efetivamente baixados). Vendas anteriores à V1.3.0 mantêm `cost_total = NULL` quando não existe informação histórica suficiente.
- Antes de consumir estoque legado sem lote, a aplicação cria um lote de abertura com o custo disponível no cadastro naquele momento; assim, os movimentos e os estornos podem devolver as unidades ao lote correto.
- O estorno restaura saldos e lotes de origem e **não altera o custo histórico**; não executa um reembolso financeiro externo.

## Dados e migração

`core.0008_cost_by_lot`:

| Entidade | Campo | Semântica |
|---|---|---|
| `StockLot` | `unit_cost` | Decimal(10,2), custo imutável por entrada |
| `StockLot` | `expiration_date` | Nulo para não perecíveis; data para perecíveis |
| `StockMovement` | `unit_cost` | Custo informado na compra; nulo em outras operações |
| `SaleItem` | `cost_total` | Custo efetivo no momento da venda, nulo para vendas antigas |
| `Product` | `purchase_price` | Referência de custo atual, NÃO preço de todo o estoque |
| `Product` | `sale_price` | Preço de venda vigente para próximas vendas |

**Migração de histórico:** os lotes já existentes recebem o `purchase_price` disponível no cadastro na data da migração. O sistema não tem como reconstruir preços reais de compras antigas sem documentos de origem. Isso deve ser tratado como **estimativa histórica**; vendas anteriores não recebem custo fictício. O saldo sem lote continua implicitamente legado até ser convertido em lote de abertura por uma operação que necessite congelar seu custo.

## Cálculo de estoque

`valor = Σ(lote.quantidade_atual × lote.unit_cost) + saldo_legado × Product.purchase_price`.

`custo médio = valor / quantidade_em_estoque`, quando positivo.

`stock-overview` e a exportação Excel passam a usar o valor por lote (com custo médio e custo de referência em colunas distintas); a tabela Estoque usa o `stock_value` desse endpoint. Estoque vencido também é valorizado pelo custo de seus respectivos lotes. **O custo médio exibido não determina o custo de cada venda**: a saída usa os lotes efetivamente consumidos.

## API

`POST /api/stock-movements/` aceita, somente para `delta > 0` e `justification = "recebimento"`:

```json
{
  "product": 17,
  "delta": 10,
  "note": "Compra fornecedor",
  "justification": "recebimento",
  "unit_cost": "8.50",
  "update_reference_cost": true,
  "new_sale_price": "16.90"
}
```

`new_sale_price` é opcional; se não for informado, mantém-se o preço atual. `update_reference_cost` padrão `false` para clientes de API antigos; no formulário, o operador pode ativá-lo. Para produto perecível, enviar também `expiration_date` no formato AAAA-MM-DD.

`GET /api/products/{id}/lots/` devolve os lotes do item, incluindo quantidades, custos, datas e indicação de lote de abertura; pode incluir um item sintético `id="legacy"` para saldo sem lote. O endpoint é autenticado em produção e não envia bytes de imagens.

## Testes e validação de implantação

- Testes de frontend: regressão de quebra de nomes, miniatura e janela do estoque, campos de compra e opções de preço, versão SemVer.
- Testes Django: custo distinto por lote, custo do saldo inicial, venda e custo congelado, custo médio e valor do estoque, rejeição de preço insuficiente, recebimentos perecíveis e edição de preço-base.
- **Obrigatório antes da publicação:** executar `pytest --cov=core`, `npm ci && npm test && npm run build`, aplicar `python manage.py migrate`, verificar a janela no mobile real e lançar compra de teste com custo diferente e eventual estorno. Fazer backup do Neon antes de migrar.
