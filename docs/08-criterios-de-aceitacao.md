# Critérios de Aceitação

## Produtos
- usuário consegue cadastrar produto;
- preço de venda é obrigatório;
- estoque não aceita valor negativo;
- validade é opcional.

## Venda
- usuário seleciona produto e quantidade;
- venda não é concluída sem estoque suficiente;
- estoque é reduzido após conclusão;
- preço usado na venda fica registrado.

## Dashboard
- mostra quantidade de vendas;
- mostra faturamento do período;
- mostra produtos em estoque crítico;
- mostra produtos próximos do vencimento;
- mostra ranking quando houver vendas;
- mostra recomendações com prioridade e motivo.

## SAD
Uma recomendação é considerada aceitável quando:
1. utiliza dados existentes no sistema;
2. possui regra conhecida;
3. informa o produto afetado;
4. apresenta ação sugerida;
5. apresenta justificativa;
6. não executa automaticamente a decisão comercial.

## Critérios adicionais da V1.2.0

1. Cadastrar produto sem foto continua possível e não altera estoque além do cadastro normal.
2. Escolher câmera/galeria apresenta prévia; a foto transmitida é JPEG e tem no máximo 102400 bytes.
3. Fotografia é nomeada por SKU seguro (ou ID), persiste após reinício e só pode ser lida por sessão autorizada em produção.
4. Substituir foto preserva exatamente uma imagem por produto. Remover foto restaura placeholder; remover novamente não provoca erro.
5. Foto inválida, vazia, maior que 100 KiB ou JPEG inválido gera HTTP 400 sem sobrescrever a anterior.
6. Falha do upload após HTTP 2xx do produto **não** apaga o produto nem cria uma cópia no próximo salvamento.
7. Notificações somem ao final da animação (1,5 s) ou no timer de fallback, sem obrigar clique no X.
8. No mobile, captura e galeria são acionáveis por toque, campos e rótulos acessíveis, sem sobreposições e sem scroll horizontal indevido.
9. Testes automatizados de frontend/backend devem passar no CI, migração no Render deve completar e fluxo real câmera → catálogo → edição → remoção deve ser testado em aparelho real antes da publicação estável.

## V1.3.0 — critérios adicionais

1. O nome do produto não quebra letra por letra quando houver foto, preços e botões no catálogo (PC e mobile).
2. A tabela Estoque carrega miniaturas autenticadas; ao tocar no nome abre janela com foto ampliada e lotes.
3. Uma entrada de recebimento de produto não perecível cria lote com `unit_cost`, mesmo sem validade.
4. Comprar o mesmo produto por R$ 5 e depois por R$ 8 mantém dois custos distintos, exibidos no detalhe e usados no valor do estoque.
5. Atualizar o custo de referência e/ou preço de venda não reescreve o preço pago nos lotes anteriores.
6. Uma venda consome o lote correto, congela `SaleItem.cost_total` e o estorno recompõe as quantidades originais.
7. Compra com custo igual ou superior ao preço de venda sem ajuste de preço é recusada sem modificar estoque.
8. A migração não atribui custos inventados a vendas anteriores; lotes antigos recebem apenas o preço de referência conhecido na data da migração.
9. Jobs do GitHub Actions (`npm ci`, `npm test`, `npm run build`, `pytest`) devem passar, e a publicação no Render exige backup e migração 0008.

## Extensão V1.4.0 — Gestão financeira

1. Faturamento após estorno não inclui venda anulada; CMV também é retirado.
2. Lucro bruto subtrai CMV histórico dos itens vendidos, e não custo atual de referência.
3. Despesas operacionais lançadas reduzem resultado; compra de estoque não reduz resultado em duplicidade.
4. Investimentos de ativos são informados sem dedução imediata de resultado.
5. Produtos/categorias filtrados não recebem todo o custo fixo da empresa.
6. Valores históricos estimados são explicitamente sinalizados.
7. XLSX possui sete abas válidas e textos não são executados como fórmulas.
8. POST com a mesma chave idempotente não gera dois lançamentos, e anulação é auditável.
9. Relatório está acessível no desktop e celular. Ver [casos e regras](25-gestao-financeira.md).

## Critérios V1.5.0

1. Cadastro e edição aceitam descrição opcional, limitada a 2000 caracteres, persistida após recarregar.
2. Todos os produtos anteriores mantêm preços, saldos, imagens e lotes após a migração.
3. O botão de salvar não fica preso após confirmação, timeout ou falha de envio da foto.
4. Um 201 confirmado não é classificado como erro de cadastro por uma falha da interface.
5. O navegador não reenvia `POST` automaticamente; o backend continua idempotente.
6. Pesquisa do catálogo apresenta um único contorno em telas claras e escuras.
7. Miniatura abre zoom, com modos cobrir e conter, sem alterar JPEG original no armazenamento.
8. URLs por seção são preservadas em F5, acessos diretos e navegação Voltar/Avançar; `/_redirects` atende ao Cloudflare Pages.
9. `npm ci`, `npm test`, build Vite e pytest Django devem passar no CI antes da liberação em produção.
