# Comercializa

Sistema de Apoio à Decisão (SAD) para lojas de variedades e pequenos comércios.

O repositório foi separado em:

- `backend/`: API em Django + Django REST Framework.
- `frontend/`: interface em Vue 3 + Vite.
- `docs/`: documentação do projeto, requisitos, visão, arquitetura, SAD e testes.

## Destaques da versão atual — Iteração 04 (30/10/2026)

- Identidade visual com variações oficiais SVG: logo vertical compacta no desktop, horizontal no celular, favicon só com símbolo e rodapé com créditos e ano automático.
- Avisos de sucesso e erro em **toast flutuante de 2 segundos**, sem mensagens permanentes ocupando a tela.
- Venda com **adicionador fixo acima do carrinho**; pesquisa e catálogo alfabético exibido ao focar.
- Visão geral com filtros gerenciais de 7/30/90 dias ou 12 meses, escolha de agrupamento e gráficos SVG em barras, linhas, área e rosca, com rankings de produtos e categorias.
- Produtos perecíveis com validade por lote no recebimento, baixa FEFO e separação de saldos físico, vendável e vencido.
- Justificativas predefinidas de estoque e campo livre para outros motivos.
- Busca por nome/SKU diretamente em cada item do carrinho de venda.
- Nova tela **Ver estoque**: saldos, nível mínimo, situação, valor das mercadorias a custo, filtros por nome, categoria e status.
- **Movimentações** separadas da posição de estoque, com justificativa e histórico.
- Pop-ups de estoque crítico, vencidos e próximos de vencer, abertos a partir do dashboard.
- Pop-up de relatórios com intervalo, categorias e itens vendidos; indicadores financeiros, ranking e visão por dia.
- Exportação de estoque e financeiro em **Excel XLSX** com múltiplas abas, formatação, filtros e cabeçalhos.
- Seed idempotente com 33 itens de loja de variedades (potes, vasilhas, bonés, chapéus, carregadores etc.).

Para detalhes dos novos lotes, gráficos e validação: [Iteração 04](docs/20-iteracao-04-experiencia-lotes-graficos-2026-10-30.md). Para identidade visual: [Iteração 03 — Identidade responsiva e rodapé](docs/19-identidade-responsiva-footer-2026-10-30.md). Para contratos de API e relatórios: [Iteração 02](docs/18-identidade-estoque-relatorios-2026-10-29.md).

**Nota:** receita após descontos não é lucro líquido (despesas e custos ainda não são subtraídos). Esta versão é somente para desenvolvimento local, pois não tem autenticação.

## Escopo desta primeira versão

A versão inicial já permite:

- cadastrar, editar, listar e excluir produtos;
- controlar estoque, estoque mínimo e validade;
- registrar vendas com múltiplos itens na API **e no carrinho da interface**;
- baixar o estoque automaticamente após uma venda e registrar trilha de auditoria;
- ajustar estoques com justificativa e consultar movimentações;
- desativar produtos sem apagar o histórico de movimentação;
- visualizar faturamento, descontos, ticket médio e quantidade de vendas;
- acompanhar a evolução diária da receita nos últimos 7 dias;
- visualizar produtos mais vendidos;
- identificar produtos com estoque crítico;
- identificar produtos com baixa movimentação;
- identificar produtos próximos do vencimento e produtos já vencidos;
- gerar recomendações iniciais de reposição e promoção.

A parte de CRUD existe principalmente para gerar os dados usados pelo módulo de apoio à decisão.

## Tecnologias

### Backend
- Python
- Django
- Django REST Framework
- SQLite

### Frontend
- Vue 3
- Vite
- Axios

## Como executar

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows CMD (recomendado Python 3.12 instalado fora da Microsoft Store):
# py -3.12 -m venv .venv
# .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`

> Se você já rodou o seed antigo de supermercado e quer ocultar aqueles itens: `python manage.py seed_demo --retire-legacy` (desativa seis SKUs específicos).
> O seed é idempotente e não modifica produtos existentes ao executar novamente.
> Os comandos acima usam dados de demonstração. Não execute `seed_demo` em uma base de produção.
> A API ainda não possui autenticação; **use somente em ambiente local de desenvolvimento** até implementar controle de acesso e configuração segura.

### 2. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173` (o Vite encaminha `/api` para `127.0.0.1:8000`).
Se necessário, defina `VITE_API_URL` para uma API externa em um `.env.local` do frontend.

## Testes

```bash
cd backend
python -m pytest
# opcional: testes Django internos (não substituem o pytest)
python manage.py test
```

No frontend (Node.js 22+):

```bash
cd frontend
npm ci
npm test
npm run build
```

**Migração obrigatória nesta atualização:** `python manage.py migrate` cria `StockLot`, `StockLotAllocation` e o campo `Product.perishable` (a tabela `StockMovement` já existia na versão anterior). Faça cópia do banco antes de migrar.
Para controle de lotes, toast e gráficos, consulte [Iteração 04](docs/20-iteracao-04-experiencia-lotes-graficos-2026-10-30.md). Para a identidade responsiva, consulte [Iteração 03](docs/19-identidade-responsiva-footer-2026-10-30.md). Para o inventário de mudanças, testes e pendências, consulte [Iteração 02](docs/18-identidade-estoque-relatorios-2026-10-29.md) e [Melhorias anteriores](docs/17-melhorias-2026-10-29.md).
Consulte também `docs/07-plano-de-testes.md`.

## Equipe

- Arthur Azevêdo

## Documentação

A documentação completa está disponível em [`docs/00-indice.md`](docs/00-indice.md).

Documentos principais do Projeto 01:

- [Documento de Visão](docs/01-visao-do-projeto.md)
- [Product Backlog — User Stories](docs/11-user-stories.md)
- [Plano Geral de Iterações](docs/12-plano-iteracoes.md)
- [Relatório do Estado Atual dos Testes](docs/13-estado-atual-testes.md)
- [Plano da Iteração 1](docs/14-iteracao-01.md)
- [Plano de Teste Geral (PTG)](docs/15-plano-teste-geral.md)
- [Plano de Teste das Iterações 1 e 2 (PTI)](docs/16-plano-teste-iteracoes-01-02.md)
