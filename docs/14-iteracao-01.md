# Plano da Iteração 1

## 1. Identificação

**Projeto:** Comercializa  
**Unidade:** I  
**Iteração:** 1  
**Duração planejada:** 15 dias  
**Período:** 06/10/2026 a 20/10/2026  
**Objetivo:** consolidar o baseline dos testes e ampliar a verificação automatizada das regras de domínio, API e cobertura do backend.

## 2. Equipe

- Arthur Azevêdo
- José Samuel
- Marcus Vinícius

## 3. User Stories da iteração

| Responsável principal | User Story | Resultado esperado |
|---|---|---|
| Arthur Azevêdo | US14 — ampliar testes automatizados dos modelos e regras de negócio | Novos cenários unitários para regras ainda pouco cobertas, mantendo a suíte sem regressões. |
| José Samuel | US15 — ampliar testes de API e integração | Cenários adicionais para endpoints e regras integradas, incluindo respostas de sucesso e erro. |
| Marcus Vinícius | US17 — acompanhar cobertura de testes | Baseline reproduzível, identificação de arquivos/linhas sem cobertura e relatório atualizado. |

## 4. Tarefas planejadas

### Arthur Azevêdo — US14

- revisar `test_models.py` e regras de domínio do módulo `core`;
- identificar cenários de limite e exceção ainda não cobertos;
- implementar novos testes unitários;
- executar a suíte após as alterações;
- documentar falhas ou débitos encontrados.

### José Samuel — US15

- revisar `test_api.py` e os endpoints atuais;
- mapear cenários de sucesso, validação e erro;
- implementar testes adicionais de integração/API;
- verificar persistência e códigos HTTP esperados;
- executar regressão dos endpoints afetados.

### Marcus Vinícius — US17

- reproduzir a execução da cobertura com `pytest-cov`;
- registrar o percentual inicial e os módulos com lacunas;
- apoiar a priorização dos trechos sem cobertura;
- medir novamente a cobertura após os novos testes;
- atualizar o relatório de estado dos testes com o resultado da iteração.

## 5. Critérios de conclusão da iteração

A Iteração 1 será considerada concluída quando:

- cada integrante tiver concluído pelo menos uma User Story sob sua responsabilidade;
- todos os testes anteriores continuarem passando;
- os novos testes estiverem versionados no repositório;
- a cobertura tiver sido novamente medida e registrada;
- eventuais falhas ou débitos técnicos encontrados estiverem documentados;
- a documentação afetada estiver atualizada.

## 6. Riscos da iteração

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Testes existentes falharem após alterações | Média | Alto | Executar regressão frequentemente e realizar mudanças pequenas. |
| Dependências ou ambiente impedirem reprodução da suíte | Média | Médio | Manter `requirements.txt`, `pytest.ini` e instruções de execução atualizados. |
| Cobertura crescer sem testar comportamento relevante | Média | Alto | Priorizar regras de negócio, erros e limites, não apenas linhas executadas. |
| Atraso na distribuição das tarefas | Baixa | Médio | Acompanhar o progresso durante a iteração e redistribuir apoio sem remover a responsabilidade principal. |

## 7. Evidências esperadas

Ao final da iteração, devem estar disponíveis no repositório:

- commits dos testes implementados;
- execução da suíte sem regressões;
- relatório de cobertura atualizado;
- documentação das lacunas encontradas;
- atualização do Product Backlog, se necessária.
