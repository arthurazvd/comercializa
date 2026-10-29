# Iteração 02 — identidade visual, estoque e análises (29/10/2026)

## Objetivo

Adequar o Comercializa à identidade visual fornecida e à rotina de uma **loja de variedades**, com leitura rápida do inventário, pesquisa eficiente na venda, relatórios de vendas filtrados e planilhas `.xlsx` formatadas.

## Funcionalidades entregues

| Área | Comportamento implementado | Cobertura automatizada |
| --- | --- | --- |
| Identidade visual | Arquivo original `frontend/public/logo-comercializa.svg`, favicon e aplicação na barra lateral | Revisão manual de logo/cores pendente |
| Tema escuro | Alternância na barra superior; preferência persistida com fallback se `localStorage` estiver indisponível | `frontend/tests/uiPreferences.test.js`; revisão visual pendente |
| Ícones | Componentes SVG locais em `frontend/src/components/AppIcon.vue`; sem dependência de CDN | Revisão visual pendente |
| Busca de itens | Cada linha do carrinho tem pesquisa por nome/SKU, seleção e indicação de saldo/preço | `frontend/tests/reportUtils.test.js`; regras de carrinho em `utils.test.js` |
| Estoque atual | Tela **Ver estoque** independente de **Movimentações**, com busca, categoria, situação, barras de saldo e valor de custo | `backend/tests/test_reports_stock.py` e `frontend/tests/reportUtils.test.js` |
| Alertas no dashboard | Cards clicáveis para estoque mínimo, vencidos e próximos do vencimento; abrem modal e navegam para estoque filtrado | `test_reports_stock.py::test_stock_overview_expired_and_expiring` |
| Vendas/financeiro | Modal com intervalo de datas, categorias, produtos, total de vendas, unidades, ticket, ranking e dias | `test_reports_stock.py::test_finance_filters_discount_pro_rata` |
| Excel | Exportação de estoque (2 abas) e vendas (4 abas), títulos, filtros, cabeçalho colorido, colunas dimensionadas, formatos de moeda | `test_reports_stock.py::test_excel_exports_produce_valid_zip` |
| Seed | 33 produtos de 9 categorias de loja de variedades; idempotente sem sobrescrever produtos já existentes | `test_reports_stock.py::test_seed_diverse_idempotent_and_non_destructive` |

## Semântica financeira — atenção

A expressão **receita após descontos** é o valor bruto dos produtos vendidos menos os descontos das vendas; ela **não é lucro líquido** nem contém custos de mercadoria, frete, despesas administrativas, tributos, comissões ou devoluções. É a métrica também chamada `revenue` nos endpoints legados.

**Quando a venda contém itens de várias categorias:** o desconto da venda é rateado proporcionalmente pelo valor bruto de cada item (com precisão Decimal). Isso evita que selecionar uma categoria desconte o valor total da venda apenas dela. O arredondamento para centavos ocorre na exibição, podendo introduzir pequenas diferenças entre subtotais agrupados e total em casos de dízimas.

**Ticket médio:** receita após descontos no filtro dividida pela quantidade de *vendas distintas* contendo ao menos um item que atende aos filtros. **Quantidade de vendas** não é número de itens.

O filtro de período é **inclusivo nas duas datas**, interpretado no fuso da instalação (`America/Fortaleza`). Os preços de venda são lidos de `SaleItem.unit_price`, ou seja, preservam os preços históricos mesmo se o cadastro atual mudar. Sem filtro informado, o padrão é o primeiro dia do mês local até hoje; o dashboard principal continua exibindo **últimos 30 dias**. Botões de período permitem mês atual e ano atual.

## API nova

Todos os endpoints seguem o mesmo prefixo `/api/` da aplicação.

- `GET /api/stock-overview/` — `{ summary: { products, units, inventory_value, low_stock_count, expired_count, expiring_count }, items: [...] }` com saldo, estoque mínimo, custo e situação.
- `GET /api/stock-export/` — arquivo `comercializa_estoque.xlsx`; abas **Estoque** e **Resumo**; saldos e custo atual.
- `GET /api/reports/finance/?start=2026-01-01&end=2026-12-31&category=3&product=10` — JSON com `filters`, `summary`, `products`, `categories`, `daily`; filtros de categoria/produto opcionais.
- `GET /api/reports/finance/export/` — mesmo conjunto de filtros, exporta `comercializa_financeiro.xlsx`; abas **Resumo financeiro**, **Produtos**, **Categorias**, **Evolução diária**.

IDs de categoria/produto inválidos e períodos inválidos retornam `400`. Intervalo superior a dez anos é rejeitado. As exportações são arquivos XLSX em Office Open XML, gerados com biblioteca padrão Python, sem novas dependências. Dados vindos do usuário são tratados como **texto**, nunca como fórmulas de Excel.

### Classificação do estoque

- `critico`: produto ativo com `stock <= minimum_stock`, inclusive saldo zero. Essa consulta pode **sobrepor** vencido/a vencer.
- `vencido`: produto ativo com saldo positivo e `expiration_date` anterior a hoje.
- `a_vencer`: produto ativo com saldo positivo e validade entre hoje e os próximos 15 dias, inclusive.
- `normal`: produto ativo fora das situações acima.
- `inativo`: produto não ativo.

O campo `status` é **único** e prioriza: inativo → vencido → a vencer → crítico → normal. Para seleção de todos os críticos, inclusive vencidos, use `low_stock`. O dashboard antigo mantém seus indicadores originais para preservar compatibilidade.

### Sobre estoque inicial

A interface de produto continua permitindo inserir o saldo de abertura no cadastro e corrigir o saldo existente (a correção cria movimentação auditada); os ajustes manuais de entradas e saídas ficam em **Movimentações**. `stock_value` usa custo unitário * saldo, sem FIFO/custo médio e sem impostos.

## Catálogo de demonstração

**Novo comando para ambiente local:**

```bash
python manage.py seed_demo
```

- Cria SKUs `UTIL-*`, `VEST-*`, `ELEC-*`, `PAP-*`, `BRIN-*`, `FEST-*`, `BELE-*`, `PET-*`, `FERR-*` apenas se ainda não existirem.
- Não altera preços, saldos nem histórico de SKUs existentes ao rodar novamente.
- Inclui algumas situações de estoque crítico, produto vencido e produto a vencer para testar pop-ups; **validade em dias é gerada em relação à data da execução**.
- Para desativar os *seis* SKUs originais de supermercado sem apagar histórico: `python manage.py seed_demo --retire-legacy`.
- Para reiniciar explicitamente os saldos da demonstração: `python manage.py seed_demo --reset-demo` (**somente testes**). Essa operação registra diferenças de saldos como movimentações de ajuste, mas não desfaz vendas já realizadas.

**Atenção:** nenhum seed deve ser executado em base de produção. O comando de demonstração não cria vendas fictícias para não contaminar índices de receita. Registre algumas vendas na interface para visualizar os relatórios.

## Como validar

```bash
# Terminal de backend, com Python e dependências instaladas
cd backend
python manage.py migrate
python manage.py check
python -m pytest
python manage.py seed_demo
python manage.py runserver

# Terminal de frontend, com Node.js instalado
cd frontend
npm ci
npm test
npm run build
npm run dev
```

Homologação visual manual: verificar logo em tela pequena, contraste dos dois temas, navegação por teclado e fechamento de pop-up com Escape; buscar um SKU na venda, escolher produto e finalizar, verificar baixa de estoque; clicar nos 3 alertas do dashboard; abrir relatório de ano anterior, filtrar produto e categoria; baixar cada XLSX e abrir no Excel/LibreOffice, conferir números e filtros.

### Execução verificada durante esta entrega

- `npm test`: **18 testes aprovados** (10 prévios, 5 de filtros e 3 de preferências).
- `python -m compileall -q backend`: **aprovado** (sintaxe de todos os `.py`).
- Validação estrutural manual do XLSX de exemplo: **XML íntegro no ZIP**.
- `pytest` de Django e `python manage.py check`: **não executados**, porque Django não está disponível neste ambiente; instalação com pip falhou.
- `npm run build`: **não executado**, porque Vite/dependências Node não estão instalados; tentativa de `npm ci` falhou com erro de rede `EAI_AGAIN`.

**Não tratar testes Django e compilação Vue como aprovados até executar `pytest` e `npm run build` localmente ou na CI.**

## Limitações e próximos passos

1. **P0 segurança:** implementar autenticação, permissões por função, DEBUG/SECRET_KEY via ambiente, controles de exportação, rate limiting e auditoria de acesso. Não publicar esta versão em produção.
2. **P1 escala:** paginação e busca server-side nas listagens; relatórios agregados em SQL ou com fila para grande volume; integração de relatórios com cancelamentos e devoluções.
3. **P1 estoque real:** cadastro de fornecedores, pedido de compra/recebimento, múltiplos depósitos, localização e lotes (validade por lote); valor de estoque a custo médio.
4. **P1 financeiro real:** custos de venda históricos, CMV, taxas, tributos, formas de pagamento, devoluções, conciliação e indicador explícito de lucro bruto/líquido quando suportado por dados.
5. **P2 qualidade:** automação de teste de navegador para tema, pop-ups e exportação; testes end-to-end com CI e acessibilidade; testes de concorrência em banco robusto.

## Arquivos novos e alterados

- `frontend/public/logo-comercializa.svg`, `frontend/src/components/AppIcon.vue`, `frontend/src/App.vue`, `frontend/src/style.css`, `frontend/src/reportUtils.js`, `frontend/src/uiPreferences.js`.
- `backend/core/export_views.py`, `backend/core/reports.py`, `backend/core/xlsx_export.py`, `backend/core/urls.py`, `backend/core/management/commands/seed_demo.py`.
- `frontend/tests/reportUtils.test.js`, `frontend/tests/uiPreferences.test.js`, `backend/tests/test_reports_stock.py`.
- Documentação: este arquivo, `README.md`, `docs/00-indice.md`, `docs/07-plano-de-testes.md`, `COMMIT_PRONTO.md`.

Não há mudança de schema nesta iteração; novas migrações não são necessárias além de `0002_stockmovement.py` da versão anterior.
