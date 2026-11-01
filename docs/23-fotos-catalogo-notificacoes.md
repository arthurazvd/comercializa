# Acesso direto às fotos e ciclo das notificações (V1.2.1)

## Comportamento visível na tela Produtos

- **Cadastro e edição**: formulário principal possui galeria, câmera, prévia, substituição e remoção.
- **Catálogo**: cada produto tem um botão **Adicionar foto** ou **Alterar foto**. A ação abre uma janela de upload sem tirar o operador do catálogo. O código usado no nome do arquivo é SKU (ou ID caso não exista SKU).
- O navegador normaliza a fotografia em JPEG quadrado com até 100 KiB, mantendo a proporção do objeto no centro e fundo branco. Uma foto inválida não é enviada.
- A janela atualiza o miniatura do produto ao receber sucesso do endpoint autenticado e mostra erro local específico se a gravação falhar.

## Notificações

- Notificações de sucesso e erros de validação utilizam uma duração de 1,5 segundo.
- O temporizador JavaScript remove o elemento da árvore; a própria notificação também tem animação de expiração visual e evento de término, cobrindo problemas de animação.
- Em preferência por movimento reduzido, a animação é dispensada e o fechamento por temporizador permanece ativo.

## Publicação e validação

- Fotos exigem **backend V1.2.0 ou posterior** no Render e migração `core.0007_product_image` aplicada no Neon.
- A melhoria do botão **Foto** e do aviso temporário é somente frontend (**V1.2.1**), podendo ser publicada no Cloudflare Pages depois do backend atualizado.
- Verificar **Versão 1.2.1** no rodapé; uma versão antiga indica deploy pendente, build não publicado ou cache desatualizado.
- A configuração `_headers` evita cache do HTML inicial no Cloudflare; bundles com hash continuam cacheáveis.
- **Critérios de aceitação**: escolher imagem de galeria, tirar foto no celular, salvar JPEG, fechar e reabrir a janela, substituir e remover; depois fazer um cadastro e verificar desaparecimento do pop-up em até cerca de 1,5 segundo.
- Os testes unitários e de contrato não substituem E2E no navegador conectado ao Render.
