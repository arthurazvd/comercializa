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
