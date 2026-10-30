# Iteração 04 — Experiência de venda, lotes perecíveis e análise gráfica

Data: 30/10/2026. Base: Comercializa, iteração 03. O objetivo foi melhorar fluidez operacional, rastreabilidade do estoque e apoio à decisão sem alterar a estrutura financeira previamente desenvolvida.

## 1. Alterações entregues

| Contexto | Comportamento após a atualização |
| --- | --- |
| Logo na barra lateral | Dimensões reduzidas para 110 × 151 px no desktop; versão horizontal no celular preservada. |
| Avisos | Notificação flutuante única para sucesso/erro, dura **2.000 ms**, novo aviso substitui o anterior e reinicia o relógio; dispensável por botão; mensagem de erro com `role=alert`. |
| Venda | Área **Adicionar item** permanece fixa no alto do formulário; produtos escolhidos ficam numa lista abaixo. |
| Catálogo da venda | Clique ou foco no campo mostra os produtos vendáveis **em ordem alfabética** mesmo sem digitação. Pesquisa por nome, SKU e categoria; limite de 60 resultados e lista com rolagem. Produtos sem quantidade vendável são omitidos. |
| Movimentações | Justificativas predefinidas: recebimento, devolução, avaria/quebra, descarte, inventário e outro; "Outro" exige explicação livre. Opções são validadas em função do sinal da quantidade na interface. A API persiste o código estruturado `StockMovement.justification` junto do texto descritivo em `note`, e valida se corresponde a entrada ou saída. Chamadas antigas sem esse campo continuam aceitas. |
| Perecíveis | Cadastro com checkbox **Produto perecível**; entrada de estoque exige **nova validade de lote**. Cada entrada com data cria um lote, preservando os anteriores. |
| Saídas | Vendas usam **FEFO**, consumindo primeiro os lotes válidos com vencimento mais próximo. Unidades vencidas não são vendáveis; baixas de avaria/descarte podem consumir lotes vencidos. |
| Consulta estoque | Separação entre saldo físico, vendável e vencido; posição de estoque e planilha XLSX incorporam colunas de risco por validade; valor a custo dos vencidos indicado. |
| Visão geral | Evolução de vendas em barras, linha, área ou rosca; 7, 30 e 90 dias e 12 meses; agrupamento por dia, semana ou mês; alternância entre receita após descontos e quantidade. |
| Itens e categorias | Gráficos individuais com escolha de apresentação e ranking, identificação da maior categoria, concentração do faturamento, quantidade e ticket médio do período. |

Os novos gráficos usam SVG nativo e CSS, sem dependências gráficas extras. Para a evolução no tempo, **linhas ou barras** mostram tendência com mais clareza; a **rosca** mostra a participação relativa de períodos. Para produtos e categorias, a rosca é particularmente útil como composição do mix.

## 2. Modelo de estoque por lote

Nova migração `core/migrations/0003_stock_lots.py`:

- `Product.perishable`: indica que recebimentos requerem data de vencimento.
- `StockLot`: produto, validade, quantidade recebida, quantidade ainda em estoque, data e movimentação de recebimento.
- `StockMovement.justification`: motivo estruturado opcional; preserva a integração de clientes antigos.
- `StockLotAllocation`: baixa de quantidade de um lote associada à movimentação. Identifica os lotes usados em uma venda, avaria ou correção.

`Product.stock` continua sendo o **saldo físico agregado**, inclusive estoque pré-existente. **A migração não apaga, redistribui nem redata saldos antigos**. Produtos existentes cujo saldo não está em lotes continuam com um saldo *legado implícito*, ao qual se aplica a validade existente no cadastro, se houver. Novas entradas perecíveis geram lotes individuais.

Fórmula: `saldo legado = saldo físico − soma das quantidades remanescentes dos lotes`; `saldo vendável = saldo legado não vencido + soma dos lotes válidos`. A API impede venda maior do que esse saldo. Para entradas de perecíveis com data passada, a API retorna erro 400. Alterações de estoque de perecíveis diretamente no cadastro não podem aumentar o saldo: recebimentos precisam ser auditados com lote.

**Regra de validade:** mercadoria recebida com validade diferente não substitui a data antiga. Se um produto tinha 3 unidades vencidas e recebe 5 unidades com validade futura, ficam 8 unidades físicas, 5 vendáveis e 3 vencidas; o recebimento é registrado com o novo vencimento e o saldo anterior mantém o seu histórico. Na consulta, um produto pode aparecer como "vencido" mesmo com saldo disponível, pois possui **parte** vencida. O alerta informa as quantidades separadamente.

As mudanças em lotes e no saldo total são atômicas via transação e atualização condicional. Caso falhe uma venda ou uma correção, a transação é revertida. `StockLotAllocation` guarda quais lotes foram baixados. O sistema ainda não implementa número do lote do fabricante, nota de entrada, fornecedor, endereço físico, custo por lote ou rastreamento de devoluções por lote: são melhorias futuras.

### API afetada

- `GET /api/products/`: novos campos `perishable`, `available_stock`, `expired_units`, `expiring_units`, `nearest_expiration`.
- `POST /api/stock-movements/`: novos parâmetros opcionais `justification` e `expiration_date` (`AAAA-MM-DD`), obrigatório para entrada quando `product.perishable = true`.
- `GET /api/stock-movements/`: campo `lots` inclui lotes recebidos ou baixados e respectivas validades.
- `GET /api/stock-overview/`: posição dos produtos com saldo disponível e em risco; resumo com `available_units` e `expired_stock_value`.
- `GET /api/stock-export/`: Excel com informações adicionais de validade e estoque vendável.
- `POST /api/sales/`: revalidação de saldo **vendável** e baixa FEFO por lote.

## 3. Como atualizar sem perder seus dados

Na pasta `comercializa`, antes de alterar banco de dados, faça backup do `backend/db.sqlite3`, se existir. **Não apague esse arquivo.**

Windows CMD — backend:

```cmd
cd backend
.venv\Scripts\activate
python manage.py migrate
python manage.py check
python -m pytest
python manage.py runserver
```

Se o ambiente Python não estiver instalado, use `py -3.12 -m venv .venv`, ative e instale com `pip install -r requirements.txt`. Se já tiver um ambiente funcionando, não precisa recriar.

Em outro terminal CMD — frontend:

```cmd
cd frontend
npm ci
npm test
npm run build
npm run dev
```

Dados demonstrativos são opcionais. `python manage.py seed_demo` cria **apenas itens ainda ausentes** e não reinicia saldos existentes. Os dois cosméticos da demonstração com validade serão cadastrados como perecíveis em instalações novas; itens anteriores podem ser marcados no formulário de edição. Não utilize `--reset-demo` com dados reais.

## 4. Testes e validação

**Executados neste ambiente:** testes de lógica do frontend via `node --test` (**33/33 aprovados**); `python -m compileall` (sintaxe de módulos Python, sem erros); conferência de tags balanceadas dos componentes Vue. Não é o mesmo que compilar o Vue nem executar o Django.

**Escritos, mas não executados neste ambiente:** testes de API `backend/tests/test_stock_lots.py` sobre recebimento, obrigatoriedade de validade, FEFO, saldo legado, descarte, alteração de saldo e seed. A instalação de Django e DRF foi bloqueada por falha de DNS ao repositório de dependências. O `npm run build` também precisa rodar em um ambiente com os pacotes do projeto disponíveis.

**Checklist manual depois de executar localmente:**

1. Abrir a tela de venda, clicar na busca vazia, observar a ordem alfabética, incluir dois produtos e confirmar que a busca continua acima dos itens.
2. Salvar uma venda e verificar toast por cerca de dois segundos; provocar erro de validação e conferir toast vermelho.
3. Criar/editar produto como perecível, abrir Movimentações, receber lote com validade futura, ver saldo e histórico.
4. Receber outro lote com validade diferente; vender menos que o saldo válido; confirmar baixa primeiro do lote que vence antes.
5. Conferir alertas de vencimento e critério de estoque crítico com saldo **disponível**, não apenas saldo físico.
6. Alternar tema e tamanhos de tela; testar mudanças de gráfico e intervalo.
7. Exportar estoque, conferir os campos de saldos vencidos e vendáveis.

## 5. Limitações e próximas prioridades

Este projeto continua adequado a **desenvolvimento local**, ainda sem autenticação, autorização, controle de caixa, custo por lote e conciliação de compras. O relatório chama de "receita após descontos" o valor bruto descontado, **não lucro líquido**. Para produção, são necessários controle de acesso, múltiplos usuários e lojas, trilhas de auditoria por operador, testes automatizados de integração no CI, validação de concorrência no banco escolhido e políticas de backup e recuperação. O controle de lote atual é operacional por data de validade, não substitui rastreabilidade documental de fornecedores.
