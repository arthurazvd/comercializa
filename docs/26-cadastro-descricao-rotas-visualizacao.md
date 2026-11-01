# Cadastro de produtos, rotas e visualização (V1.5.0)

## Objetivo e limites

A aplicação conserva o fluxo de criação/edição em uma operação de persistência e, opcionalmente, uma operação separada para a foto. Após retorno HTTP de sucesso, o frontend atualiza a lista local sem solicitar uma confirmação extra ao endpoint `operations`. Uma falha de imagem ou interface não invalida o cadastro já confirmado. O formulário tem `finally` para liberar o botão mesmo quando uma etapa posterior lança exceção.

## Campos de produto

- Nome (obrigatório, até 150 caracteres).
- **Descrição** (opcional, até 2.000 caracteres), armazenada no campo textual `Product.description`. Pode ser preenchida e atualizada pelo operador. Não modifica preço, saldo nem SKU.
- Categoria, SKU, preço de compra, preço de venda, estoque, estoque mínimo, validade, perecibilidade, situação e imagem seguem as regras existentes.
- A descrição aparece como resumo no catálogo e completa nos detalhes do estoque e na visualização ampliada da fotografia.

## UC — Cadastro com resposta tardia ou falha posterior

1. Operador preenche o formulário e salva.
2. Cliente envia uma única requisição de escrita, com chave de idempotência para `POST`.
3. Recebido HTTP 2xx, registra o ID e mostra o produto na lista, mesmo que a sincronização posterior falhe.
4. Se houver imagem, envia-a por chamada separada. Falha de imagem conserva o ID e abre caminho para nova tentativa sem recadastrar o produto.
5. Se a API não responder em até 40 segundos para o produto ou 30 segundos para a foto, o formulário deixa de indicar carregamento e orienta conferir o catálogo. Não afirma que houve sucesso sem confirmação.
6. Ao repetir manualmente os mesmos dados de cadastro não confirmado, o backend usa a mesma chave para proteger contra duplicidade.

**Regra de negócio:** a exceção de uma atualização da interface não desfaz a operação confirmada. O sistema não deve repetir automaticamente o POST.

## UC — Visualizar foto

1. Operador abre o catálogo ou os detalhes do produto no estoque.
2. Clica/toca na miniatura da imagem; a aplicação abre uma janela de visualização.
3. Pode alternar entre **Preencher espaço** (corte puramente visual com `object-fit: cover`) e **Ver foto inteira** (`object-fit: contain`).
4. O arquivo JPEG armazenado não sofre nova compressão ou edição durante a visualização. Ao retornar aos detalhes do estoque, o diálogo anterior permanece disponível.
5. Produto sem imagem mostra placeholder e não abre uma imagem inexistente.

## URLs da aplicação

| Seção | URL relativa |
|---|---|
| Visão geral | `/visao-geral` |
| PDV / Vendas | `/vendas` |
| Produtos | `/produtos` |
| Estoque | `/estoque` |
| Movimentações | `/movimentacoes` |
| Financeiro (janela) | `/financeiro` |

- `history.pushState` atualiza a URL na navegação sem recarregar a página.
- `popstate` sincroniza a seção ao usar Voltar/Avançar do navegador.
- O aplicativo lê o caminho inicial, portanto recarregar a aba mantém a seção.
- Cloudflare Pages precisa servir `index.html` para rotas internas (arquivo `frontend/public/_redirects`).
- A seção acessada continua protegida pelo mesmo login da aplicação. O endereço não ignora a autenticação.

## Migração de dados e retrocompatibilidade

`0010_product_description` adiciona um campo `TEXT NOT NULL DEFAULT ''`, mantendo todos os produtos já existentes sem alteração de preços ou saldos. O serializer aceita ausência do campo para clientes antigos. Aplicar a migração após backup, antes do frontend V1.5.0.

## Testes e critérios de aceitação

- Nova suíte `frontend/tests/navigation-and-product-v150.test.js`: mapeamento de rotas, proteção de fluxo pós-salvamento, modelo de descrição e CSS de miniaturas e busca.
- Nova suíte `backend/tests/test_product_description_v150.py`: criação, edição, persistência, campo opcional e limite de caracteres.
- Verificação manual obrigatória: com o serviço Render acordando, salvar produto, editar sem duplicação, adicionar foto, abrir no catálogo/estoque, usar links diretos e Voltar/Avançar no celular e desktop.
- Os testes automáticos não substituem o build Vite e a execução de `pytest` no GitHub Actions.
