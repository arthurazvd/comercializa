# Plano de Teste Geral (PTG) — Comercializa

## 1. Identificação

**Projeto:** Comercializa  
**Responsável:** Arthur Azevêdo  
**Disciplina:** Teste de Software — 2026.2

## 2. Objetivo

Este Plano de Teste Geral define a estratégia de garantia da qualidade do Comercializa durante o semestre. O objetivo é reduzir regressões, verificar as regras de negócio do backend e fornecer evidências reproduzíveis sobre o comportamento do sistema, a cobertura automatizada e a integração entre API, persistência e módulo de apoio à decisão (SAD).

## 3. Escopo dos testes

### 3.1 Incluído

- modelos e regras de domínio do módulo `core`;
- CRUD de categorias e produtos;
- registro de vendas e cálculo de valores;
- atualização de estoque após vendas;
- endpoints da API REST;
- indicadores e recomendações do SAD;
- fluxos funcionais representativos;
- tratamento de entradas inválidas e regras de limite;
- execução automatizada da suíte e medição de cobertura.

### 3.2 Fora do escopo atual

- testes de carga e estresse em ambiente de produção;
- testes E2E completos em navegador real;
- testes específicos de infraestrutura de produção;
- funcionalidades ainda não implementadas no produto.

## 4. Níveis de teste adotados

| Nível | Objetivo | Evidência principal |
|---|---|---|
| Unidade | Verificar modelos, cálculos, validações e regras isoladas. | `backend/tests/test_models.py` e cenários de serviços/SAD. |
| Integração | Verificar interação entre API, serviços, ORM e banco de dados. | `backend/tests/test_api.py` e testes integrados do SAD. |
| Sistema/Aceitação | Verificar fluxos completos relevantes para o usuário. | `backend/tests/test_acceptance.py`. |

## 5. Estratégia

A estratégia combina testes automatizados de regressão com inspeção contínua de cobertura e análise estática. Para cada User Story trabalhada, os critérios de aceitação são convertidos em cenários verificáveis. Casos positivos, negativos e de limite são priorizados nas regras críticas, especialmente venda, estoque e recomendações do SAD.

Os testes devem ser executados localmente antes do envio de alterações e novamente no GitHub Actions a cada `push` ou `pull_request` para `main`. A cobertura é produzida em XML para consumo pelo SonarQube.

## 6. Ferramentas

| Ferramenta | Uso |
|---|---|
| `pytest` | Execução da suíte automatizada. |
| `pytest-django` | Integração dos testes com Django. |
| `pytest-cov` / Coverage.py | Medição e geração do relatório de cobertura. |
| `factory-boy` | Construção de dados de teste. |
| GitHub Actions | Integração contínua. |
| SonarQube LABENS | Análise estática e acompanhamento de métricas de qualidade. |
| Django REST Framework test utilities | Verificação dos endpoints REST. |

## 7. Ambiente e dados de teste

Os testes do backend são executados em Python com dependências definidas em `backend/requirements.txt`. O Django utiliza banco de dados isolado de testes criado durante a execução. Fixtures e factories devem produzir dados determinísticos e independentes, evitando dependência de dados manuais do ambiente de desenvolvimento.

Comando de referência:

```bash
cd backend
pytest --cov=core --cov-report=term-missing --cov-report=xml:coverage.xml
```

## 8. Cobertura

A cobertura deve ser registrada em todas as iterações relevantes. O baseline documentado no início da disciplina é de **73 testes aprovados e 72% de cobertura**. A meta é não reduzir a cobertura sem justificativa e ampliar prioritariamente a cobertura de comportamentos críticos, em vez de perseguir apenas percentual de linhas executadas.

O arquivo `backend/coverage.xml` é a fonte utilizada pelo SonarQube por meio de `sonar.python.coverage.reportPaths`.

## 9. Papéis e responsabilidades

Como o grupo é individual, **Arthur Azevêdo** concentra os papéis de desenvolvimento e QA, mantendo separação lógica entre implementação, execução dos testes e revisão das evidências.

| Papel | Responsabilidade |
|---|---|
| Desenvolvimento | Implementar/corrigir funcionalidades e manter testes relacionados. |
| QA | Planejar casos, executar regressão, analisar falhas e registrar evidências. |
| CI/Qualidade | Manter workflow, cobertura e integração com SonarQube. |
| Documentação | Atualizar planos, resultados e débitos técnicos. |

## 10. Critérios de entrada

Uma atividade está pronta para teste quando:

- requisitos ou critérios de aceitação estão identificados;
- código necessário está disponível em versão executável;
- dependências podem ser instaladas;
- ambiente de teste pode ser inicializado;
- dados necessários podem ser criados por fixture/factory.

## 11. Critérios de saída

Uma User Story/iteração é considerada testada quando:

- casos planejados foram executados;
- testes automatizados relacionados estão passando;
- não existem falhas críticas conhecidas sem registro;
- regressão relevante permanece aprovada;
- cobertura foi gerada e analisada;
- defeitos e débitos técnicos encontrados estão documentados;
- CI conclui os testes com sucesso.

## 12. Critérios de suspensão e retomada

Os testes podem ser suspensos quando o ambiente estiver indisponível, houver falha impeditiva de dependência/migração ou defeito bloqueador que inviabilize os cenários seguintes. A execução é retomada após correção e validação mínima do ambiente.

## 13. Gestão de defeitos

Falhas encontradas devem ser reproduzíveis e registradas com comportamento observado, comportamento esperado, contexto e evidência. Correções devem incluir teste de regressão sempre que tecnicamente viável.

## 14. Riscos de qualidade

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Regressão em estoque após venda | Média | Alto | Testes unitários, integração e aceitação do fluxo de venda. |
| Cálculos financeiros incorretos | Média | Alto | Cenários de valores, quantidades e descontos. |
| Recomendações incorretas do SAD | Média | Alto | Testes determinísticos para cada regra e justificativa. |
| Cobertura alta sem comportamento relevante | Média | Médio | Priorizar critérios de aceitação, limites e erros. |
| CI/Sonar indisponível | Baixa/Média | Médio | Manter execução local reproduzível e registrar evidências. |

## 15. Evidências e relatórios

As evidências são compostas pelos arquivos de teste versionados, saída do GitHub Actions, `coverage.xml`, métricas do projeto no SonarQube LABENS e documentos de planejamento/estado dos testes em `docs/`.
