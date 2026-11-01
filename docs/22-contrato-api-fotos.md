# Contrato de API — Fotos de produtos (V1.2.0)

## Rotas e autenticação

As rotas compartilham o mecanismo de autenticação da API do Comercializa. Em produção, enviar cabeçalho `Authorization: Token <TOKEN>`; nunca colocar token na URL. O frontend usa `axios` autenticado para buscar um Blob, pois `<img src>` direto não envia o cabeçalho. É vedado expor os bytes em listagens.

| Método | Rota | Entrada | Saída |
|---|---|---|---|
| GET | `/api/products/{id}/` | — | `has_image: boolean`, `image_updated_at: ISO|null` e campos do produto |
| GET | `/api/products/{id}/image/` | — | `image/jpeg` binário (404 se ausente) |
| PUT | `/api/products/{id}/image/` | `multipart/form-data`, arquivo no campo `image` | 200, `has_image`, `image_updated_at`, `filename`, `size` |
| DELETE | `/api/products/{id}/image/` | — | 200, `has_image: false`, `image_updated_at: null` (idempotente) |

**Validação na API:** conteúdo inicial JPEG `FF D8 FF`, formato real identificado por Pillow, bytes 1–102400, dimensão máxima de 4096 por eixo. Resposta `400` (`image`) para ausência/erro/limite, `404` para produto inexistente ou foto não encontrada e `401/403` quando sessão não autorizada. Chave de autenticação permanece sensível.

**Normalização no browser:** insumo `image/*` até 20 MiB, Canvas branco quadrado, primeiro tenta lado de 800 px e reduz progressivamente até 128 px; qualidade JPEG variável; seleciona primeira combinação ≤100 KiB. O arquivo é apresentado como `SKU.jpg` ou `produto.jpg` localmente e renomeado definitivamente pelo servidor para `SKU.jpg` ou `<id>.jpg`. Alteração de SKU muda o nome lógico armazenado.

**Consistência:** `POST /api/products/` ou `PUT /api/products/{id}/` é finalizado antes do upload da foto. Falha do segundo passo não desfaz o produto. O formulário mantém o ID em caso de erro para repetição segura. Os dados binários estão no Neon PostgreSQL (tabela `ProductImage`, campo `data`), não no disco local. O cliente obtém miniaturas sob demanda; a URL Blob é temporária e descartada ao desmontar.

**Limite de capacidade:** 10.000 imagens no teto de 100 KiB consomem aproximadamente 0,98 GB **apenas em bytes**, antes de índices e outros dados. Esta implementação é adequada para catálogos pequenos, não para 20.000 imagens no Neon gratuito. Para escala grande, planejar object storage, migração e backups antes de importar todas as fotos.
