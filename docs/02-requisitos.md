# Especificação de Requisitos

## Requisitos funcionais

**RF01 — Gerenciar categorias**  
O sistema deve permitir cadastrar, consultar, alterar e remover categorias.

**RF02 — Gerenciar produtos**  
O sistema deve permitir cadastrar, consultar, alterar e remover produtos.

**RF03 — Controlar estoque**  
Cada produto deve possuir quantidade atual e estoque mínimo.

**RF04 — Controlar validade**  
Produtos perecíveis podem possuir data de validade.

**RF05 — Registrar vendas**  
O usuário deve conseguir registrar uma venda contendo um ou mais produtos.

**RF06 — Atualizar estoque**  
Ao concluir uma venda, o estoque deve ser reduzido automaticamente.

**RF07 — Impedir estoque negativo**  
O sistema não deve concluir uma venda cuja quantidade seja superior ao estoque disponível.

**RF08 — Histórico de vendas**  
O sistema deve manter histórico das vendas e itens vendidos.

**RF09 — Identificar produtos mais vendidos**  
O SAD deve calcular ranking de produtos por quantidade vendida.

**RF10 — Identificar estoque crítico**  
O SAD deve identificar produtos com estoque igual ou inferior ao estoque mínimo.

**RF11 — Priorizar reposição**  
O SAD deve recomendar reposição utilizando estoque atual, estoque mínimo e velocidade de venda.

**RF12 — Identificar baixa movimentação**  
O SAD deve indicar produtos sem vendas ou com baixa saída em determinado período.

**RF13 — Detectar risco de vencimento**  
O SAD deve identificar produtos próximos da validade.

**RF14 — Recomendar ação promocional**  
O SAD deve sugerir avaliação de promoção quando houver baixa movimentação ou risco de vencimento.

**RF15 — Dashboard gerencial**  
O sistema deve exibir indicadores, alertas, rankings e recomendações.

**RF16 — Tendências**  
Em evolução posterior, o SAD deverá comparar períodos para detectar crescimento ou queda na demanda.

**RF17 — Classificação por relevância**  
Em evolução posterior, o SAD deverá classificar produtos por participação no faturamento e movimentação.

## Requisitos não funcionais

**RNF01 — Usabilidade:** interface simples para usuários sem conhecimento técnico.  
**RNF02 — Responsividade:** interface utilizável em desktop e dispositivos móveis.  
**RNF03 — Integridade:** operações de venda devem preservar consistência do estoque.  
**RNF04 — Desempenho:** consultas comuns devem responder em tempo adequado para pequenos comércios.  
**RNF05 — Manutenibilidade:** backend e frontend devem permanecer separados.  
**RNF06 — Explicabilidade:** recomendações do SAD devem apresentar o motivo da recomendação.  
**RNF07 — Segurança:** versões de produção deverão utilizar autenticação, autorização, HTTPS e proteção de dados.  
**RNF08 — Auditabilidade:** vendas devem manter os preços utilizados no momento da transação.

## Regras de negócio

**RN01:** estoque não pode ficar negativo.  
**RN02:** o preço do item vendido deve ser preservado na venda mesmo que o preço do produto seja alterado depois.  
**RN03:** produto com estoque menor ou igual ao mínimo entra em estado crítico.  
**RN04:** produto próximo do vencimento deve gerar alerta conforme janela configurada.  
**RN05:** recomendação deve informar ação e justificativa.  
**RN06:** produtos sem venda no período de análise podem ser classificados como baixa movimentação.

## Requisitos implementados e refinados — V1.2.0

**RF21 — Foto de produto:** no cadastro e na edição, permitir selecionar fotografia da galeria ou capturar pela câmera, com prévia. A foto é opcional; salvar o produto sem foto deve funcionar.

**RF22 — Padronização:** a foto deverá ser convertida para `image/jpeg`, enquadrada sem deformar a proporção em fundo branco, em dimensão quadrada de até 800×800 px (podendo diminuir para caber) e tamanho máximo de 102.400 bytes. O nome gerado no servidor deverá usar o código SKU sanitizado (`CODIGO.jpg`), ou ID quando não houver SKU.

**RF23 — Persistência e segurança:** permitir uma foto por produto, com substituição e exclusão, armazenada no banco persistente; leitura/upload/remoção autenticados em produção. Não incluir os bytes de fotos no JSON da listagem de produtos.

**RF24 — Separação de falhas:** se o cadastro já tiver retorno HTTP 2xx, eventual falha posterior na foto não deve desfazer o produto nem gerar novo produto ao reenviar. A tela deve preservar o ID e informar especificamente a falha da foto.

**RF25 — Mensagens:** toasts de sucesso/erro devem desaparecer automaticamente em 1,5 segundo, no fim da barra animada, com opção de fechar manualmente. Os erros de campos inválidos continuam sendo apresentados.

**RF26 — Usabilidade do PDV:** adicionar produto que já está no carrinho soma a quantidade sem criar linha duplicada; respeita o saldo; controles `+` e `−` em campos numéricos mobile.

**RF27 — Gráficos:** evolução das vendas em barras; dez itens mais vendidos por unidades em rosca, sem 11º/“Outros”; categorias em rosca. Cartões em tamanho estável e listas extensas com scroll vertical temático.

**RF28 — Layout e sessão:** sidebar estática no desktop, navegação inferior mobile, tema claro/escuro, sessão autenticada em produção, versionamento SemVer (`1.2.0`).

**RNF01 — Resiliência:** indisponibilidade das consultas de leitura não pode ser confundida com falha de gravação confirmada. **RNF02 — Capacidade:** fotos de até 100 KB ocupam espaço no PostgreSQL, portanto o armazenamento é adequado apenas ao volume suportado pela instância. **RNF03 — Acessibilidade:** botões de câmera/galeria, estado de prévia e imagens possuem rótulos, foco navegável e fallback.

## Requisitos funcionais V1.3.0

- RF-FOTO-EST: apresentar miniatura autenticada na tabela de estoque e pré-visualização ao abrir o produto.
- RF-LOTE-CUSTO: registrar custo unitário em cada nova compra, sem sobrescrever o custo dos lotes anteriores.
- RF-PRECO: permitir atualizar separadamente o custo de referência e o preço de venda; preço de venda precisa superar o custo do novo recebimento.
- RF-VALORIZACAO: calcular o valor e o custo médio do estoque por lotes, preservando saldo legado a custo de referência.
- RF-HIST-CUSTO: congelar o custo das unidades consumidas na venda; preservar lotes e custos durante estorno.

Consulte [detalhamento UC13–15](24-custos-por-lote-e-previsualizacao-de-estoque.md).

## Extensão implementada V1.4.0 — Financeiro

Ver requisitos **RF-FIN-01 a RF-FIN-12**, fórmulas, diferenciação entre lucro e caixa e restrições de alocação em [Gestão financeira](25-gestao-financeira.md).
