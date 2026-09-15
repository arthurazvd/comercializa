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
