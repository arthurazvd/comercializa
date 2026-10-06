# Product Backlog — User Stories

## 1. Objetivo

Este documento apresenta o Product Backlog do **Comercializa**, organizado em histórias de usuário que orientam a evolução do sistema durante a disciplina de Teste de Software.

## 2. Perfis considerados

- **Comerciante:** proprietário ou responsável pelo pequeno comércio que utiliza o sistema no dia a dia.
- **Gestor:** usuário interessado nos indicadores, alertas e recomendações do módulo de apoio à decisão.
- **Equipe de desenvolvimento:** responsável pela manutenção, evolução, qualidade e testes do sistema.

## 3. Histórias de usuário

| ID | História de usuário | Prioridade | Critérios de aceitação resumidos |
|---|---|---|---|
| US01 | Como comerciante, quero cadastrar e manter categorias para organizar os produtos do estabelecimento. | Alta | Permitir criar, listar, editar e remover categorias, respeitando as validações definidas. |
| US02 | Como comerciante, quero cadastrar e manter produtos para controlar os itens comercializados. | Alta | Permitir CRUD de produtos com preços, estoque, estoque mínimo, categoria, validade e situação. |
| US03 | Como comerciante, quero registrar vendas com um ou mais itens para manter o histórico comercial atualizado. | Alta | Registrar venda, itens, quantidades, preços e desconto, calculando subtotal e total corretamente. |
| US04 | Como comerciante, quero que o estoque seja atualizado automaticamente após uma venda para evitar divergências. | Alta | Reduzir estoque após venda e impedir operação que resulte em estoque negativo. |
| US05 | Como gestor, quero visualizar um dashboard com indicadores do negócio para acompanhar rapidamente a situação do comércio. | Alta | Exibir faturamento, quantidade de vendas, rankings, alertas e indicadores relevantes. |
| US06 | Como gestor, quero identificar produtos com estoque crítico para priorizar a reposição. | Alta | Listar produtos cujo estoque esteja igual ou abaixo do mínimo e apresentar justificativa. |
| US07 | Como gestor, quero visualizar os produtos mais vendidos para entender a demanda. | Média | Apresentar ranking calculado a partir dos itens vendidos em período analisado. |
| US08 | Como gestor, quero identificar produtos com baixa movimentação para avaliar ações comerciais. | Média | Identificar produtos sem vendas ou com baixa saída no período configurado. |
| US09 | Como gestor, quero receber alertas de produtos próximos do vencimento para reduzir perdas. | Alta | Identificar produtos dentro da janela de vencimento e apresentar o motivo do alerta. |
| US10 | Como gestor, quero receber recomendações de reposição para melhorar as decisões de compra. | Alta | Considerar estoque atual, mínimo e movimentação, exibindo ação e justificativa. |
| US11 | Como gestor, quero receber recomendações promocionais para produtos com baixa saída ou risco de vencimento. | Média | Sugerir avaliação de promoção quando as regras do SAD forem satisfeitas. |
| US12 | Como gestor, quero analisar produtos por participação no faturamento para identificar itens mais relevantes. | Média | Implementar classificação ABC ou mecanismo equivalente com resultado verificável. |
| US13 | Como gestor, quero comparar períodos de vendas para identificar tendências de crescimento ou queda. | Média | Permitir comparação entre períodos e apresentar a variação de forma compreensível. |
| US14 | Como equipe de desenvolvimento, quero ampliar os testes automatizados dos modelos e regras de negócio para reduzir regressões. | Alta | Testar caminhos principais, limites e erros das regras de domínio. |
| US15 | Como equipe de desenvolvimento, quero ampliar os testes de API e integração para garantir o funcionamento conjunto dos componentes. | Alta | Cobrir endpoints principais, códigos HTTP, persistência e regras integradas. |
| US16 | Como equipe de desenvolvimento, quero manter testes de aceitação para validar os principais fluxos sob a perspectiva do usuário. | Alta | Automatizar cenários representativos de cadastro, venda e uso do SAD. |
| US17 | Como equipe de desenvolvimento, quero acompanhar a cobertura de testes para identificar trechos sem verificação automatizada. | Alta | Gerar relatório de cobertura reproduzível e registrar a evolução ao longo das iterações. |
| US18 | Como equipe de desenvolvimento, quero executar os testes automaticamente no CI para detectar regressões a cada alteração. | Alta | Workflow deve instalar dependências, executar testes e falhar quando a suíte falhar. |

## 4. Definition of Done

Uma User Story é considerada concluída quando:

1. seus critérios de aceitação forem atendidos;
2. o código estiver integrado ao repositório do projeto;
3. os testes automatizados relacionados estiverem implementados ou atualizados;
4. a suíte de testes relevante estiver passando;
5. a documentação afetada estiver atualizada;
6. não houver regressão conhecida introduzida pela alteração.
