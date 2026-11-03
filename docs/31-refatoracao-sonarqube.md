# Correção dos apontamentos SonarQube — 03/11/2026

## Objetivo

Reduzir duplicação e complexidade cognitiva **sem modificar as regras de venda, estoque, custos por lote, relatórios ou estorno**. O scanner só marcará os apontamentos como resolvidos após uma nova análise.

## Relação dos apontamentos tratados

| Módulo | Alteração aplicada |
|---|---|
| `export_views.py` | Extraída constante `GROSS_PROFIT_LABEL` para o rótulo de lucro bruto no Excel. |
| `bootstrap_admin.py` | Variável `User` renomeada para `user_model`, sem alterar o cadastro administrativo. |
| `reports.py` | `finance_report` decomposta em apuração por venda, rateio de desconto, agrupamento de resultados, compras e lançamentos financeiros. |
| `serializers.py` | Validação de entrada separada em justificativa/validade e custo/preço; gravação de movimentação dividida em revalidação, atualização de estoque e registros de lote. |
| `services.py` | Recomendações de reposição, validade e baixa movimentação extraídas para funções específicas; constante `PRIORITY_MEDIUM`. |
| `stock_lots.py` | Seleção de lotes elegíveis e baixa por FEFO extraídas, mantendo checagens de concorrência. |
| `views.py` | Exceção redundante removida; conversão `list()` dispensável no estorno retirada. |
| `xlsx_export.py` | Geração de célula e de linha extraída, preservando o XML dos arquivos XLSX. |

## Testes e evidências

- Frontend: `npm test` — **98 aprovados** nesta preparação.
- Arquivos Python: `compileall` — sintaxe aprovada.
- Exportação Excel: comparação byte a byte dos componentes XML gerados pela versão anterior e pela versão refatorada, com entradas representativas — **idênticos**.
- YAML dos GitHub Actions — estrutura válida.
- **Pendente:** execução completa de `pytest` e `mutmut` no GitHub Actions, cobertura >=70% e reanálise do Quality Gate do SonarQube.

## Correção do fluxo de mutação

A execução anterior do `mutmut` 3.x coletou **156 testes passando, mas zero testes associados a mutantes**. Por isso, aquele resultado não é score de mutação válido. Esta entrega fixa `mutmut==2.5.1`, usa o modo de mutação *in-place* e mantém os arquivos críticos `core/services.py` e `core/stock_lots.py` no escopo. A ferramenta altera temporariamente o código da branch de CI, restaura-o e executa os testes para comparar o comportamento. O job mantém artefatos TXT/XML e falha diante de erro da execução.

**Não confundir:** uma taxa de **70% de cobertura** é requisito do `pytest-cov`, não uma meta de 70% de mutação (que a atividade não especificou).

## Após publicar na branch `feature/testes-mutacao`

1. Conferir `Backend | testes e cobertura >= 70%` e `Frontend | testes e build` no Actions.
2. Rodar `Testes de mutação (sob demanda)` e baixar os artefatos de mutação.
3. Executar nova análise SonarQube e conferir `New issues` e `Quality Gate`. O scanner ter sucesso no envio não é aprovação do Quality Gate.
4. Registrar os resultados e links em [`30-validacao-e-evidencias.md`](30-validacao-e-evidencias.md).
5. Abrir PR `feature/testes-mutacao → develop` para preservar o histórico GitFlow.
