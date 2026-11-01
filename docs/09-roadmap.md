# Roadmap

## Fase 1 — Base operacional
- [x] estrutura backend/frontend/docs;
- [x] produtos;
- [x] categorias;
- [x] estoque mínimo;
- [x] validade;
- [x] registro de venda;
- [x] baixa automática de estoque.

## Fase 2 — SAD inicial
- [x] dashboard;
- [x] estoque crítico;
- [x] ranking de vendas;
- [x] baixa movimentação;
- [x] validade;
- [x] recomendações explicáveis.

## Fase 3 — Gestão comercial
- [ ] fornecedores;
- [ ] entrada de mercadorias;
- [x] movimentações de estoque com trilha de auditoria;
- [x] múltiplos itens com interface de carrinho;
- [ ] promoções;
- [ ] relatórios por período.

## Fase 4 — SAD intermediário
- [ ] classificação ABC;
- [ ] análise de margem;
- [ ] tendência de vendas;
- [ ] parametrização das regras;
- [ ] score de prioridade;
- [ ] feedback sobre recomendações.

## Fase 5 — SAD avançado
- [ ] previsão de demanda;
- [ ] sazonalidade;
- [ ] comparação entre modelos;
- [ ] avaliação quantitativa das recomendações.

## Melhorias de robustez — 29/10/2026
- [x] validação de descontos, vencimento e estoque nas vendas;
- [x] transações e atualização condicional de saldos;
- [x] auditoria de ajuste manual e alteração no cadastro;
- [x] dashboard com ticket médio, receita diária e vencidos;
- [x] interface responsiva com filtros e histórico;
- [x] suíte unitária frontend e job CI;
- [ ] autenticação, autorização e preparação para produção (**prioridade crítica**);
- [ ] testes E2E em navegador, concorrência real e cobertura completa;
- [ ] paginação, filtros de período, fornecedores e entradas de compra.

Detalhes e evidências: [17-melhorias-2026-10-29.md](17-melhorias-2026-10-29.md).

## Melhorias futuras além da V1.2.0

- Migrar `ProductImage.data` de banco relacional para object storage S3-compatible (como R2/Neon Object Storage), com backup e migração dos arquivos existentes, caso o volume supere a quota do PostgreSQL.
- Implementar testes browser E2E (Playwright) cobrindo navegação por teclado, câmera simulada, progressão dos toasts e carrinho.
- Cobrir cenários de múltiplos operadores e instabilidade no upload de foto; monitorar taxas de falha, ocupação de banco e tempos de consulta.
- Integração bancária de reembolso (hoje estorno apenas interno).
