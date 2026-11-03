# GitFlow, GitHub Actions, SonarQube e Milestone

## 1. Fluxo de branches

- **`main`**: entregas publicadas e estáveis.
- **`develop`**: integração das novas mudanças.
- **`feature/testes-mutacao`**: branch de implementação desta atividade, criada **a partir de `develop`**.
- **`release/*`**: preparação de versões que serão incorporadas à `main`.
- **`hotfix/*`**: correções urgentes saindo de `main` e integradas novamente a `develop`.

Exemplo para a primeira entrega (não altere `main` diretamente):

```bash
git switch main
git pull origin main
git switch -c develop
# se develop já existir no remoto: git fetch origin && git switch develop
git push -u origin develop
git switch -c feature/testes-mutacao
git add .
git commit -m "ci: documenta mutacao e exige cobertura 70%"
git push -u origin feature/testes-mutacao
```

Depois, abra um Pull Request de **`feature/testes-mutacao` → `develop`**, confira os jobs, revise e faça merge. Para publicar, abra **`develop` → `main`** através de uma `release/*`, conforme a política da equipe. Se `develop` já existe, atualize essa branch em vez de recriá-la.

## 2. Milestone no GitHub (ação manual de gerente ou maintainer)

A criação de milestone depende de permissão no repositório. Abra **Issues → Milestones → New milestone**:

- **Título:** `Testes de Mutação`
- **Descrição sugerida:** `Planejar, configurar, executar e documentar testes de mutação no Comercializa. Inclui cobertura >=70%, relatório mutmut, análise SonarQube nas aulas, evidências no GitHub Actions e PR via GitFlow.`
- **Prazo:** conforme o cronograma do professor (não inventar data).
- **Issues sugeridas:** configuração do mutmut; primeira execução e evidências; mutantes sobreviventes e melhoria de testes; validação SonarQube e cobertura; revisão documental.

Associe as issues e o PR ao milestone. Link depois de criado: `https://github.com/arthurazvd/comercializa/milestones`.

Alternativa via GitHub CLI, com autenticação `gh auth login` concluída:

```bash
gh api repos/arthurazvd/comercializa/milestones \
  -f title="Testes de Mutação" \
  -f description="Planejar e executar mutmut, registrar sobreviventes, cobertura >=70%, SonarQube em aula e PR via GitFlow."
```

**Status nesta entrega:** foi preparado o procedimento e o conteúdo do milestone, **mas ele não foi criado remotamente**. O ZIP não contém permissões de acesso ao GitHub.

## 3. GitHub Actions

A pipeline `.github/workflows/tests.yml` executa automaticamente em commits `main`, `develop`, `feature/**`, `release/**` e `hotfix/**`, além de PRs para `main/develop`. Há botão manual `Run workflow` para executar em aula.

| Job | Verificação | Requisito |
|---|---|---|
| Frontend | `npm ci`, `npm test`, `npm run build` | Sem falhas |
| Backend | `pytest`, cobertura `core` com XML e `--cov-fail-under=70` | Sem falhas e **>=70%** |
| SonarQube | Scanner oficial com `sonar-project.properties` e `backend/coverage.xml` | Token/servidor configurados e análise concluída |

O scan **não é silenciosamente pulado** quando falta token/URL: o job informa a configuração ausente. Por segurança, PR de repositório externo não recebe secrets do SonarQube. O escopo de cobertura é o **Python do backend**; não declarar cobertura de frontend antes de instrumentá-la.

## 4. Configuração do SonarQube

1. Criar/encontrar o projeto com **project key `comercializa`** no SonarQube da instituição. A chave usada no projeto e a URL precisam coincidir com a configuração real do servidor.
2. Em GitHub → **Settings → Secrets and variables → Actions**, adicionar secrets:
   - `SONAR_TOKEN`: token criado no SonarQube para o projeto.
   - `SONAR_HOST_URL`: URL base acessível pelo GitHub-hosted runner (ex.: `https://sonar.exemplo.edu.br`).
3. Rodar a pipeline em `develop` ou manualmente em dia de aula e conferir o resultado no SonarQube; anexar link da análise à issue do milestone.
4. Se o SonarQube da faculdade só for acessível por VPN/rede interna, um runner hospedado pelo GitHub **não terá acesso** sem rota de rede; será necessário runner self-hosted da instituição ou servidor acessível externamente. Nunca publique tokens no README.

## 5. Execução nos dias de aula

Não há calendário das aulas no repositório, então **nenhum agendamento automático foi inventado**. Em cada dia letivo:

1. Abra **Actions → Testes, cobertura e SonarQube → Run workflow** e selecione `develop` ou a branch do trabalho.
2. Confira a cobertura >=70% e scan do SonarQube.
3. Se for aula dedicada à mutação, execute **Testes de mutação (sob demanda)** e documente a taxa. No primeiro envio de `feature/testes-mutacao`, a mutação também será iniciada por push, mesmo antes de o workflow estar na branch padrão.
4. Registre data, commit, links, valores e prints na tabela abaixo ou na issue do milestone.

| Data da aula | Branch / SHA | Cobertura backend | SonarQube (link) | Mutação (link, se houver) |
|---|---|---|---|---|
| *a preencher* | *a preencher* | — | — | — |

## 6. Checklist da entrega acadêmica

- [ ] Criar milestone `Testes de Mutação` no GitHub e associar issue e PR.
- [ ] Subir branch `feature/testes-mutacao` e abrir PR para `develop`.
- [ ] Configurar secrets e confirmar job SonarQube no Actions.
- [ ] Executar e anexar evidências das aulas.
- [ ] Obter CI verde e cobertura >=70% no commit final.
- [ ] Executar mutmut ao menos uma vez e registrar resultados reais.
- [ ] Revisar o manual e enviar o link do repositório.

[GitHub do projeto](https://github.com/arthurazvd/comercializa) · [Plano de Testes](07-plano-de-testes.md) · [Testes de Mutação](27-testes-de-mutacao.md) · [Manual](28-manual-de-execucao.md)
