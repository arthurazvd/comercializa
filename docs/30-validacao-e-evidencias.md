# Validação da entrega — testes, CI e SonarQube

## Verificações realizadas na preparação dos arquivos

- **Frontend:** `npm test` executado sobre a V1.5.0 do ZIP em 03/11/2026, **98 aprovados, 0 falhas**.
- **Python:** compilação sintática de `backend/core/` e `backend/tests/` concluída.
- **Arquivos de CI:** configuração YAML dos dois workflows interpretada e estrutura de jobs conferida.
- **Documentação:** links relativos do README, índice e documentos novos conferidos.
- **Configuração de mutação:** `backend/pyproject.toml` interpretado corretamente.

## Evidências pendentes, não presumidas

- **Cobertura real do backend nesta versão:** não aferida neste ambiente, pois a instalação do Django foi impedida por falta de acesso ao índice Python. A CI inclui `--cov-fail-under=70`; o percentual válido será o reportado pelo workflow após o push.
- **`npm ci` e build Vite:** não executados, pois faltam pacotes no cache npm offline. O job do GitHub deve validá-los.
- **Mutação:** configurada, mas ainda não executada; registrar quantidades e escore após o primeiro job real.
- **SonarQube:** análise não disparada nesta preparação, pois precisa do token, da URL e de acesso ao servidor institucional. O botão manual permite registrar execução em cada aula.
- **Milestone e branches remotas:** não criados pelo ZIP; exigem autenticação/permissão na conta GitHub. A documentação contém os passos e comandos.

Anexar nesta página, após a publicação, links do Actions, URL do SonarQube, percentual medido, resultado do mutmut e link do Pull Request. Não substituir resultados ausentes por estimativas.


## Refatoração dos apontamentos SonarQube (03/11/2026)

Foram alterados os módulos `core/reports.py`, `core/services.py`, `core/stock_lots.py`,
`core/serializers.py`, `core/xlsx_export.py`, `core/export_views.py`,
`core/views.py` e `core/management/commands/bootstrap_admin.py`.
A intenção é reduzir a complexidade cognitiva por extração de responsabilidades,
sem alterar as regras financeiras, de estoque, vendas ou estorno.

**Validação pendente:** rodar `pytest` completo, conferir cobertura >=70%,
executar `mutmut run` e confirmar fechamento dos apontamentos no Quality Gate
SonarQube após enviar commit na `feature/testes-mutacao`.
Não registrar os 11 apontamentos como resolvidos no SonarQube antes de nova análise.
