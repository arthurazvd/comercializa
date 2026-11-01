# Gestão financeira — V1.4.0

## Finalidade

Permitir que o gestor acompanhe desempenho de vendas, custo histórico da mercadoria vendida (CMV), lucro bruto, despesas operacionais, compras de estoque e investimentos em ativos, com filtros por período e exportação Excel. O módulo fornece uma **visão gerencial aproximada**, não uma DRE fiscal ou fluxo de caixa auditado.

## Requisitos funcionais e regras de negócio

- **RF-FIN-01 — Faturamento:** total de vendas válidas a preço de venda histórico, antes dos descontos. Estornos integrais não entram nos valores correntes do relatório.
- **RF-FIN-02 — Receita após descontos:** faturamento menos descontos rateados proporcionalmente entre itens. Evitar chamar de lucro líquido.
- **RF-FIN-03 — CMV:** somar `SaleItem.cost_total` registrado no momento da venda. Não substituir custo histórico por `Product.purchase_price` atual. Para itens históricos anteriores à V1.3.0 sem `cost_total`, usar custo de referência apenas como **estimativa sinalizada** e contar linhas estimadas.
- **RF-FIN-04 — Lucro bruto e margem:** `lucro_bruto = receita_apos_descontos - CMV`; `margem_bruta = lucro_bruto / receita_apos_descontos × 100` (zero para receita zero).
- **RF-FIN-05 — Despesas:** registrar despesa operacional com categoria, descrição, data e valor positivo. É permitido anular, preservando registro e autor. Total de despesa somado apenas para visão da empresa inteira.
- **RF-FIN-06 — Resultado operacional estimado:** lucro bruto menos despesas operacionais cadastradas no período. Não é lucro líquido contábil; pode não incluir todas as despesas e impostos.
- **RF-FIN-07 — Compras de estoque:** somar valor recebido por movimentações com justificativa `recebimento` e delta positivo, pelo `StockMovement.unit_cost` histórico. Quando ausente, usar referência com marcação de estimativa. Compra aumenta estoque e **não** é deduzida novamente do lucro bruto; apenas o CMV das unidades vendidas é reconhecido no resultado.
- **RF-FIN-08 — Investimento em ativo:** equipamento, estrutura ou bem durável registrado manualmente em tipo `investment`, separado das despesas. Não é despesa operacional imediata (depreciação não modelada).
- **RF-FIN-09 — Exportação:** `GET /api/reports/finance/export/` gera XLSX com sete abas: Resumo financeiro, Produtos, Categorias, Evolução diária, Compras de estoque, Despesas e Investimentos. Descrição é texto XML escapado, nunca fórmula executável.
- **RF-FIN-10 — Filtros:** período (datas inclusivas), categoria e produto. Receitas, CMV, lucro bruto e compras seguem o filtro de produto/categoria. Despesas gerais **não** são atribuídas arbitrariamente a um SKU; em filtro específico o resultado operacional retorna `null` e o frontend mostra “—”.
- **RF-FIN-11 — Consistência:** estorno remove conjuntamente receita e CMV da venda; lançamentos manuais anulados deixam de contar. `Idempotency-Key` nos POSTs protege contra duplicidade por reenvio.
- **RF-FIN-12 — Usabilidade:** KPIs no dashboard; botão Financeiro na navegação; formulário de lançamentos e consulta no modal, acessível em desktop e mobile.

## Casos de uso

### UC-FIN-01 — Conferir lucro bruto

1. Abra **Financeiro** pelo menu ou painel.
2. Escolha início e fim; opcionalmente categoria ou produto.
3. O sistema exibe faturamento, descontos, receita, CMV, lucro bruto, margem e nível de estimativa dos custos legados.
4. Compare resultados por produto, categoria e dia.

### UC-FIN-02 — Registrar despesa operacional

1. Abra Financeiro e o formulário de lançamentos.
2. Selecione tipo **Despesa operacional**; informe categoria, descrição, valor positivo e data.
3. O sistema salva e recalcula despesas e resultado no período.
4. Em caso de erro de lançamento, clique **Anular**; a linha é ocultada do cálculo, mas mantida no banco para auditoria.

### UC-FIN-03 — Registrar investimento em ativo

1. No formulário, escolha **Investimento em ativo**; informe descrição, categoria, valor e data.
2. O investimento aparece separadamente do lucro bruto e das despesas operacionais.
3. A aquisição de mercadoria **não** precisa ser digitada aqui: é inferida das entradas de estoque (cuidado com duplicidades manuais).

### UC-FIN-04 — Exportar Excel

1. Selecione o período e filtros.
2. Clique **Exportar Excel completo**.
3. Salve a planilha XLSX; dados, despesas, compras e os avisos de estimativa ficam em abas próprias.

## Modelo de dados

`FinancialEntry` (`id`, `kind` expense/investment, `category`, `description`, `amount`, `entry_date`, `created_at`, `created_by`, `voided_at`, `voided_by`), criado na migração `0009_financial_entries`. A anulação é *soft-void*, não deleção física. Compras decorrem de `StockMovement`, custos históricos de `StockLot.unit_cost` e do `SaleItem.cost_total` já criados na V1.3.0.

## API

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/api/reports/finance/?start=YYYY-MM-DD&end=YYYY-MM-DD` | KPIs e detalhes por período, com filtros opcionais category/product |
| GET | `/api/reports/finance/export/` | XLSX de sete abas com os mesmos filtros |
| GET | `/api/finance/entries/?start=...&end=...` | Despesas e investimentos não anulados |
| POST | `/api/finance/entries/` | Cadastrar lançamento manual, aceita `Idempotency-Key` |
| POST | `/api/finance/entries/{id}/void/` | Anular de forma idempotente, sem apagar histórico |

## Premissas e limites

- Não registra contas a pagar/receber, pagamentos de fornecedores, liquidação de cartões, taxas, impostos de todas as operações nem fluxo de caixa bancário.
- Valores de compras representam **recebimentos registrados**, não comprovação de pagamento; investimentos manuais não comprovam pagamento externo.
- No modelo simplificado, resultado operacional não considera depreciação, encargos faltantes ou tributos não cadastrados.
- Não inferir custo histórico real para vendas anteriores à implantação do CMV congelado. A estimativa pode variar com o preço cadastrado atual.
- Não modificar dados anteriores na migração de lançamento financeiro; base anterior permanece intacta.

## Testes e liberação

Testes adicionais: `backend/tests/test_financial_v140.py` (cálculo de CMV por lote, desconto, estorno, despesas, investimentos, filtro por produto, anulação, idempotência, validação, histórico estimado, estrutura Excel), `frontend/tests/finance-v140.test.js` (contratos estáticos de interface). Antes da publicação, executar `pytest` completo, `npm ci`, `npm test`, `npm run build` e `python manage.py makemigrations --check --dry-run` no GitHub Actions. Fazer backup do Neon antes de aplicar a migração 0009. Teste manual no celular e com compras/estornos em ambiente de homologação.
