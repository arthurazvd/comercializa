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
