# Plano de Testes

## 1. Objetivo

Definir como o Comercializa será verificado para garantir que funcionalidades operacionais e recomendações do SAD funcionem de maneira consistente.

## 2. Escopo

Nesta etapa serão testados:
- produtos;
- estoque;
- vendas;
- integridade das transações;
- dashboard;
- regras iniciais do SAD.

## 3. Tipos de teste

### Testes unitários
Validam regras isoladas e cálculos.

### Testes de integração
Validam API, banco de dados e atualização de estoque.

### Testes funcionais
Validam os fluxos do ponto de vista do usuário.

### Testes de aceitação
Validam se o comportamento atende aos requisitos.

### Testes do SAD
Validam se os mesmos dados de entrada geram indicadores, prioridades e justificativas esperadas.

## 4. Casos de teste principais

| ID | Cenário | Resultado esperado |
|---|---|---|
| CT01 | Cadastrar produto válido | Produto salvo |
| CT02 | Editar produto | Dados atualizados |
| CT03 | Excluir produto sem dependência | Produto removido |
| CT04 | Registrar venda com estoque | Venda salva e estoque reduzido |
| CT05 | Vender acima do estoque | Operação recusada |
| CT06 | Produto atinge estoque mínimo | Dashboard marca estoque crítico |
| CT07 | Produto vence em 3 dias | SAD gera alerta de validade |
| CT08 | Produto sem venda em 30 dias | SAD indica baixa movimentação |
| CT09 | Produto com estoque crítico | SAD recomenda reposição |
| CT10 | Venda registrada | Ranking e indicadores podem ser atualizados |

## 5. Critérios de aprovação

- nenhuma venda pode gerar estoque negativo;
- estoque deve ser atualizado na mesma transação da venda;
- recomendações devem possuir justificativa;
- regras do SAD devem produzir resultados determinísticos para os mesmos dados;
- testes automatizados críticos devem passar antes de integrar mudanças.

## 6. Automação atual

Execute:

```bash
cd backend
python manage.py test
```

A primeira suíte cobre:
- criação de produto;
- baixa de estoque;
- bloqueio de estoque insuficiente;
- estoque crítico;
- alerta de validade.

## 7. Testes futuros

- testes E2E do Vue;
- testes de autenticação;
- carga;
- segurança;
- usabilidade com comerciante real;
- validação das recomendações com dados históricos reais.
