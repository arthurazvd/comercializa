# Design Doc — US15: Ampliação dos Testes de API e Integração com Mock Objects

**Data:** 17/11/2026  
**Autor:** Hildemberg (hildemberg986)  
**Contexto:** Tarefa T02 — Iteração 1 (Engenharia de Software e Garantia de Qualidade)  
**Status:** Aprovado  

---

## 1. Contexto e Motivação

Durante a Iteração 1 da disciplina de Teste de Software, o objetivo central foi consolidar o baseline dos testes automatizados e ampliar a verificação de domínio, regras e APIs. O discente Arthur Azevêdo focou na US14 (regras de modelos com mocks).

A **US15** complementa e expande a cobertura técnica da Iteração 1, focando em:
1. Ampliação dos testes de integração de API via Django REST Framework (`APIClient`).
2. Testes unitários com isolamento estrito via **Mock Objects** (`unittest.mock.patch`, `MagicMock`).
3. Verificação de códigos de status HTTP (200, 201, 400, 404) e payloads de erro.
4. Garantia da integridade referencial e transacional da persistência.

---

## 2. Estratégia de Testes

### 2.1 Testes Unitários com Mock Objects (`backend/tests/test_us15_api_mocks.py`)
- Uso de `unittest.mock.patch` para isolar chamadas de banco e serviços de cálculo de faturamento, estoque crítico e velocidade de vendas.
- Simulação de exceções de integridade (`ProtectedError`) e validação da resposta tratada pelo viewset.
- Validação isolada de serializadores sem tocar no banco de dados.

### 2.2 Testes de Integração de API
- Criação e validação de produtos e categorias via endpoints REST.
- Verificação de persistência real e verificação de não persistência em casos de erro 400.
- Teste de exclusão protegida com produtos vinculados a itens de venda (`SaleItem`).

---

## 3. Auditoria Cruzada de QA (Arthur Azevêdo — US14)

- Elaboração de `docs/qa/relatorio-qa-us14-arthur.md`.
- Execução dos cenários de aceitação da US14 (regras de faturamento, recomendação de reposição para estoque mínimo e reflexo no dashboard).
- Registro detalhado de evidências e parecer de aceitação.
