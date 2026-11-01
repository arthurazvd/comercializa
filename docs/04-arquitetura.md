# Arquitetura

## Visão geral

```text
┌───────────────────────────┐
│       Vue 3 + Vite        │
│ Interface / Dashboard SAD │
└─────────────┬─────────────┘
              │ HTTP / JSON
              ▼
┌───────────────────────────┐
│ Django REST Framework     │
│ API + regras de negócio   │
├───────────────────────────┤
│ Serviço de Apoio à Decisão│
│ indicadores/recomendações │
└─────────────┬─────────────┘
              │ ORM
              ▼
┌───────────────────────────┐
│          SQLite           │
│ produtos / vendas / itens │
└───────────────────────────┘
```

## Backend

Responsável por:
- persistência;
- validações;
- transações de venda;
- regras de estoque;
- cálculo dos indicadores;
- geração das recomendações do SAD.

## Frontend

Responsável por:
- cadastro e edição de produtos;
- registro de vendas;
- dashboard;
- apresentação das recomendações e justificativas.

## Módulo SAD

Nesta primeira versão está implementado como um serviço de regras transparentes no backend. Isso facilita explicar por que cada recomendação foi gerada.

Futuramente esse serviço pode incorporar:
- classificação ABC;
- média móvel;
- sazonalidade;
- previsão de demanda;
- modelos estatísticos;
- aprendizado de máquina.

## Arquitetura de produção V1.2.0

```text
Cloudflare Pages  →  Vue 3 + Vite (mobile/desktop)
      │ HTTPS + token, JSON / multipart JPEG
      ▼
Render Web Service (Django + DRF + Gunicorn)
      │ Transações, validações, consultas, relatórios
      ▼
Neon PostgreSQL (produtos, vendas, lotes, estornos, ProductImage até 100 KB)
```

**Desenvolvimento:** SQLite local; **produção:** PostgreSQL Neon. O desenho inicial do documento com SQLite refere-se ao ambiente local, não ao deploy atual. O backend valida o JPEG com Pillow, usa `ProductImage.data` em `BinaryField` e retorna os bytes apenas em `GET /api/products/{id}/image/`. A lista de produtos expõe somente `has_image` e `image_updated_at`. No frontend, fotos são requisitadas com o mesmo token e renderizadas por URL temporária de Blob, apenas ao aparecer na tela (`IntersectionObserver`). As URLs temporárias são liberadas na desmontagem.

**Render gratuito não possui disco persistente:** fotografias armazenadas no filesystem local seriam perdidas em deploy/sleep. Banco persistente resolve a durabilidade básica; usar object storage externo será necessário para grande volume de imagens e deverá ser introduzido por migração explícita. O plano gratuito Neon possuía limite de 1 GB de armazenamento de banco por projeto na documentação de outubro/2026; monitorar quota e backups. A estimativa de 10 mil fotos × 100 KiB ultrapassa 0,95 GiB sem considerar índices, dados e overhead.

**Segurança:** login com token na produção; `GET/PUT/DELETE image` seguem as permissões padrão. CORS restrito aos domínios configurados; não persistir tokens no nome de imagem; não expor blobs no JSON.

## Extensão V1.4.0 — Serviço financeiro

Na implantação atual, o frontend Vue é publicado no Cloudflare Pages, o backend Django no Render e os dados PostgreSQL no Neon (o diagrama SQLite acima representa o ambiente inicial de desenvolvimento). `core.reports.finance_report` apura receita/CMV por `SaleItem.cost_total`; `StockMovement` fornece o valor das compras e `FinancialEntry` os lançamentos manuais. `core.export_views` converte o relatório em XLSX pelo gerador OOXML existente. API protegida por autenticação em produção. Ver [especificação financeira](25-gestao-financeira.md).
