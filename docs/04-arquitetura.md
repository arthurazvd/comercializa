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
