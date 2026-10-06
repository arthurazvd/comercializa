# Plano da Iteração 1

## 1. Identificação

**Projeto:** Comercializa  
**Unidade:** I  
**Iteração:** 1  
**Duração planejada:** 15 dias  
**Período:** 06/10/2026 a 20/10/2026  
**Responsável:** Arthur Azevêdo  
**Objetivo:** consolidar o baseline dos testes e ampliar a verificação automatizada das regras de domínio, API e cobertura do backend.

## 2. User Stories da iteração

| Responsável | User Story | Resultado esperado |
|---|---|---|
| Arthur Azevêdo | US14 — ampliar testes automatizados dos modelos e regras de negócio | Novos cenários unitários para regras ainda pouco cobertas, sem regressões. |
| Arthur Azevêdo | US15 — ampliar testes de API e integração | Cenários adicionais para endpoints e regras integradas. |
| Arthur Azevêdo | US17 — acompanhar cobertura de testes | Baseline reproduzível e relatório de cobertura atualizado. |

## 3. Tarefas planejadas

### US14 — Testes de domínio
- revisar `test_models.py` e regras do módulo `core`;
- identificar cenários de limite e exceção;
- implementar/ajustar testes unitários;
- executar regressão.

### US15 — Testes de API e integração
- revisar `test_api.py` e endpoints atuais;
- mapear sucesso, validação e erro;
- implementar/ajustar testes de integração/API;
- verificar persistência e códigos HTTP.

### US17 — Cobertura
- reproduzir a cobertura com `pytest-cov`;
- registrar o percentual inicial e lacunas;
- gerar `coverage.xml`;
- comparar a cobertura após os ajustes.

## 4. Critérios de conclusão

A Iteração 1 será considerada concluída quando:

- Arthur tiver concluído pelo menos uma User Story planejada;
- todos os testes anteriores continuarem passando;
- novos testes/ajustes estiverem versionados;
- cobertura tiver sido medida e registrada;
- falhas ou débitos encontrados estiverem documentados;
- documentação afetada estiver atualizada.

## 5. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Regressões após alterações | Média | Alto | Executar a suíte frequentemente e manter mudanças pequenas. |
| Ambiente impedir reprodução | Média | Médio | Manter dependências e instruções atualizadas. |
| Cobertura crescer sem testar comportamento relevante | Média | Alto | Priorizar regras, erros e limites. |
| Acúmulo de atividades por grupo individual | Média | Médio | Priorizar histórias críticas e registrar débitos de forma explícita. |

## 6. Evidências esperadas

- commits dos testes/documentos;
- suíte sem regressões;
- relatório de cobertura;
- registro das lacunas encontradas;
- atualização do backlog quando necessária.
