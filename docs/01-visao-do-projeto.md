# Documento de Visão

## 1. Identificação

**Projeto:** Comercializa  
**Tipo:** Sistema de Apoio à Decisão para Pequenos Comércios  
**Plataforma:** Web

## 2. Descrição do problema

Pequenos comerciantes tomam decisões frequentes sobre reposição, promoções, estoque e produtos perecíveis. Quando os dados estão dispersos ou não são analisados, as decisões dependem quase exclusivamente da memória e experiência do responsável pelo estabelecimento, aumentando o risco de ruptura de estoque, excesso de mercadorias, perda por validade e decisões comerciais pouco fundamentadas.

## 3. Visão da solução

O Comercializa é um sistema web que coleta dados operacionais do comércio e os transforma em indicadores, alertas, prioridades e recomendações. O cadastro de produtos e o registro de vendas formam a base operacional, enquanto o principal valor do sistema está no módulo de Sistema de Apoio à Decisão (SAD).

## 4. Objetivo geral

Desenvolver um sistema web capaz de apoiar decisões de pequenos comerciantes utilizando dados de estoque, vendas, preços, movimentação e validade.

## 5. Objetivos específicos

- identificar estoque crítico;
- priorizar reposições;
- identificar produtos mais e menos vendidos;
- detectar baixa movimentação;
- detectar risco de perda por vencimento;
- sugerir promoções;
- analisar participação dos produtos no faturamento;
- apresentar tendências de vendas;
- evoluir para previsão de demanda;
- apresentar informações em painel gerencial simples.

## 6. Perfis de usuários e personas

### Persona 1 — Proprietário do comércio

Responsável pela administração do estabelecimento e pelas decisões de compra, reposição e promoção. Precisa visualizar rapidamente a situação do negócio sem depender de conhecimento técnico ou de análise manual de dados.

**Necessidades:** indicadores simples, alertas, recomendações explicáveis e visão geral das vendas e do estoque.

### Persona 2 — Responsável operacional

Pessoa que realiza cadastros, acompanha o estoque e registra as vendas no sistema. Precisa de operações simples, consistentes e rápidas para evitar divergências nos dados.

**Necessidades:** cadastro de produtos e categorias, registro de vendas, controle de estoque e validações claras.

### Persona 3 — Gestor

Usuário interessado principalmente nas informações gerenciais e no apoio à decisão. Analisa produtos mais vendidos, estoque crítico, baixa movimentação, validade e recomendações.

**Necessidades:** dashboard, rankings, alertas e justificativas para as recomendações apresentadas.

## 7. Escopo

### 7.1 Dentro do escopo inicial

- produtos e categorias;
- estoque e estoque mínimo;
- validade;
- registro e histórico de vendas;
- baixa automática de estoque;
- dashboard gerencial;
- ranking de produtos;
- alertas de estoque crítico e validade;
- identificação de baixa movimentação;
- recomendações de reposição e promoção baseadas em regras.

### 7.2 Fora do escopo inicial

- emissão fiscal;
- integração com maquininha;
- contas a pagar/receber;
- gestão completa de fornecedores;
- autenticação avançada;
- previsão de demanda por IA;
- aplicativo móvel nativo.

Esses itens podem ser incorporados em versões futuras.

## 8. Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | Gerenciar categorias. |
| RF02 | Gerenciar produtos. |
| RF03 | Controlar estoque atual e estoque mínimo. |
| RF04 | Controlar validade de produtos perecíveis. |
| RF05 | Registrar vendas com um ou mais produtos. |
| RF06 | Atualizar automaticamente o estoque após a venda. |
| RF07 | Impedir operações que resultem em estoque negativo. |
| RF08 | Manter histórico de vendas e itens vendidos. |
| RF09 | Identificar produtos mais vendidos. |
| RF10 | Identificar produtos com estoque crítico. |
| RF11 | Priorizar e recomendar reposições. |
| RF12 | Identificar produtos com baixa movimentação. |
| RF13 | Detectar produtos com risco de vencimento. |
| RF14 | Recomendar avaliação de ações promocionais. |
| RF15 | Exibir dashboard gerencial com indicadores e recomendações. |
| RF16 | Comparar períodos para identificar tendências de demanda. |
| RF17 | Classificar produtos por relevância no faturamento e movimentação. |

A especificação detalhada encontra-se em [02-requisitos.md](02-requisitos.md).

## 9. Requisitos não funcionais

| ID | Requisito |
|---|---|
| RNF01 | Usabilidade: interface simples para usuários sem conhecimento técnico. |
| RNF02 | Responsividade: interface utilizável em desktop e dispositivos móveis. |
| RNF03 | Integridade: operações de venda devem preservar a consistência do estoque. |
| RNF04 | Desempenho: consultas comuns devem responder adequadamente para pequenos comércios. |
| RNF05 | Manutenibilidade: backend e frontend devem permanecer separados e organizados. |
| RNF06 | Explicabilidade: recomendações do SAD devem informar o motivo da recomendação. |
| RNF07 | Segurança: versões de produção devem utilizar autenticação, autorização, HTTPS e proteção de dados. |
| RNF08 | Auditabilidade: vendas devem preservar os preços utilizados no momento da transação. |

## 10. Benefícios esperados

- reduzir rupturas de estoque;
- reduzir perdas por validade;
- evitar excesso de produtos sem saída;
- melhorar decisões de compra;
- identificar oportunidades promocionais;
- fornecer visão mais clara do negócio.

## 11. Premissas e restrições

- o sistema é direcionado inicialmente a pequenos comércios;
- a qualidade das recomendações depende da consistência dos dados registrados;
- a primeira versão utiliza regras determinísticas no SAD;
- funcionalidades avançadas devem ser adicionadas incrementalmente;
- novas funcionalidades devem preservar as regras de negócio e ser acompanhadas por testes automatizados.

## 12. Riscos

| ID | Risco | Probabilidade | Impacto | Estratégia de mitigação |
|---|---|---|---|---|
| R01 | Dados de vendas ou estoque incorretos comprometerem as recomendações. | Média | Alto | Aplicar validações, testes de integração e regras de consistência. |
| R02 | Baixa cobertura de testes permitir regressões. | Média | Alto | Medir cobertura continuamente e priorizar regras críticas. |
| R03 | Recomendações do SAD serem pouco compreensíveis ao usuário. | Média | Médio | Exibir ação sugerida acompanhada da justificativa. |
| R04 | Crescimento do escopo comprometer as entregas do semestre. | Média | Alto | Manter backlog priorizado e respeitar o escopo de cada iteração. |
| R05 | Divergências entre frontend e API causarem falhas de integração. | Média | Médio | Manter contratos claros e testes de API/integração. |
| R06 | Dependência excessiva de dados históricos limitar análises futuras. | Baixa | Médio | Evoluir funcionalidades analíticas conforme a base de dados amadurecer. |
