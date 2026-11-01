## Comercializa V1.3.0 — Fotos no estoque e custo por lote (01/11/2026)

- Catálogo: layout em grade corrige nomes comprimidos ao lado de fotos e ações.
- Estoque: fotos autenticadas, clique no nome para pré-visualização ampliada, indicadores e histórico de lotes.
- Movimentações: recebimentos com custo unitário específico por lote, controle de custo de referência e alteração opcional de preço de venda; preços anteriores não são reescritos.
- Estoque é valorizado por custo de cada lote; saída de venda registra custo histórico e estorno devolve ao lote de origem. Lotes podem não ter validade.
- **Publicação exige backend e migração `0008_cost_by_lot` no Neon antes de publicar o novo frontend**. Faça backup do banco. As fotos existentes não mudam.
- Os testes locais de frontend e sintaxe Python não substituem `npm ci`, build Vite e `pytest` no GitHub Actions, nem teste real no Render.

Documentação funcional: [UC13–15 e contrato API](docs/24-custos-por-lote-e-previsualizacao-de-estoque.md).

---

## Comercializa V1.2.3 — Correção do npm e teste de movimentação (01/11/2026)

- O lockfile apontava para `picocolors@1.2.0` (tarball inexistente no npm), embora seu hash fosse o da versão publicada `1.1.1`. Corrigidas a versão e a URL.
- O `postcss@8.5.28` estava incorretamente registrado como dependente de `picocolors@^1.2.0`; a faixa correta é `^1.1.1`.
- Novo teste estático `frontend/tests/lockfile-consistency.test.js` é executado pelo Actions **antes** do `npm ci` e também pelo `npm test`. Ele verifica versões e URLs de tarballs e evita regressões.
- O teste Django de confirmação da movimentação agora envia `note`, que já era obrigatório para a API de estoque. Há também um teste garantindo que `note` ausente continua sendo rejeitado sem mexer no estoque nem registrar a operação.
- **Não houve alteração nos modelos, nas regras do servidor ou na API.** Nenhuma migração nova.
- Versão exibida no aplicativo: `1.2.3`. O código deve ser publicado no Cloudflare Pages; testes Django devem ser aprovados no GitHub antes de promover para produção.

**Validação disponível:** testes Node do frontend e checagens estruturais dos arquivos. A instalação completa `npm ci`, o build Vite e a suíte Django precisam passar no GitHub Actions, pois este ambiente está sem acesso ao registry npm e não tem Django instalado.

---

## Comercializa V1.2.2 — Integridade do pipeline e prevenção de duplicidade

Esta correção mantém os recursos da V1.2.1 (fotos no catálogo e avisos temporários) e ajusta o pipeline do GitHub Actions:

- O `frontend/package-lock.json` foi corrigido para a dependência publicada `es-object-atoms@^1.1.1` exigida por `get-intrinsic@1.3.0`.
- Vendas e movimentações agora passam pelo `IdempotentCreateMixin` antes de gravar; antes suas implementações próprias de `create()` ignoravam esse mixin.
- A mesma `Idempotency-Key` devolve a resposta original sem duplicar venda/estoque, com histórico de confirmação consultável.
- Frontend identificado como **Versão 1.2.2**. Não há migração nova; é necessário publicar o **backend no Render** e o **frontend no Cloudflare Pages** a partir deste código.

Validação obrigatória: aguarde a aprovação dos dois jobs do GitHub Actions (`npm ci`, testes, build, `pytest`) antes de publicar. Para detalhes dos casos de teste consulte [Plano de Testes](docs/07-plano-de-testes.md). O ambiente de desenvolvimento do patch não teve acesso ao registro npm nem ao Django; verificar a CI é indispensável.

---

## Comercializa V1.2.1 — Botão de fotos no catálogo e avisos temporários

Agora cada item do **Catálogo** oferece **Adicionar foto / Alterar foto** (sem precisar entrar no cadastro), com câmera, galeria e miniatura. O cadastro de produtos mantém o editor de imagens. Os avisos visuais expiram após **1,5 segundo** tanto por temporizador como por animação; mensagens realmente persistentes de erro de login são exibidas no formulário, não são pop-ups.

**Importante:** para usar imagens, publicar o backend V1.2.0 ou superior no Render e executar a migração `core.0007_product_image` no banco Neon. Depois publicar a V1.2.1 no Cloudflare Pages. Confirmar **Versão 1.2.1** no rodapé. Se ainda mostrar V1.1.0, a nova interface não foi implantada no site. Confira os deploys e faça recarregamento completo. Consulte [documentação da funcionalidade](docs/23-fotos-catalogo-notificacoes.md).

---

# Comercializa

Sistema de Apoio à Decisão (SAD) para lojas de variedades e pequenos comércios.

O repositório contém `backend/` (Django/DRF), `frontend/` (Vue/Vite) e `docs/` (documentação).


## Funcionalidade de fotos de produtos — V1.2.0 (01/11/2026)

Na tela **Produtos**, agora é possível escolher foto da galeria ou tirar foto com a câmera, visualizar a prévia, substituir ou remover durante a edição. O navegador a converte em JPEG quadrado (fundo branco, proporção preservada), com até **100 KB** e nome por **SKU** (ou ID quando ausente). Fotos aparecem como miniaturas no catálogo e são consultadas de forma autenticada sob demanda.

**Deploy obrigatório de frontend E backend:** executar migração `0007_product_image` no banco Neon (o `backend/build.sh` já roda `migrate`) e publicar o Vue atualizado no Cloudflare Pages. Instalar a dependência Python `Pillow` no Render. Backup do banco antes da migração. Em caso de falha da foto após salvar o produto, ele permanece cadastrado e a interface preserva o ID para reenvio.

**Armazenamento:** fotos são guardadas no banco Neon, nunca no disco efêmero do Render. Controle a quota: até 100 KB por imagem parece pouco, mas 10 mil imagens podem ultrapassar 1 GB. Para catálogos grandes, recomenda-se storage de objetos antes de uma importação massiva. Consulte [arquitetura](docs/04-arquitetura.md), [casos de uso](docs/03-casos-de-uso.md), [API](docs/22-contrato-api-fotos.md) e [matriz de testes](docs/21-matriz-rastreabilidade-campos.md).

**Notificações:** toast desaparece ao fim da animação de 1,5 segundo, com fallback por timer e opção de dispensa manual. A correção preserva erros HTTP de validação e evita mensagens falsas de cadastro.


## Atualização 1.1.0 — interface e vendas (01/11/2026)

- **Versionamento SemVer:** versão `1.1.0` no rodapé e no `package.json`. As próximas correções podem seguir `1.2.0`, `1.1.2` etc.; novas funcionalidades podem usar `1.2.0`.
- **Vendas:** selecionar e incluir novamente o mesmo item soma a quantidade à linha original, sem duplicar produtos. Respeita o estoque vendável e os lotes disponíveis.
- **Mobile:** controles `−` e `+` para campos numéricos (quantidade, estoque, preços e desconto). O campo digitável continua disponível.
- **Notificações:** duração de 1.500 ms para sucessos e erros, com fechamento manual opcional.
- **Gráficos:** evolução em barras; ranking e participação de categorias em rosca. O ranking exibe **apenas os dez produtos mais vendidos por quantidade**, sem “Outros”; os percentuais representam o total desses dez. O painel de ranking tem rolagem vertical interna e altura limitada.
- **Layout:** painéis da primeira linha alinhados em altura; scrollbars temáticas claro/escuro; barra lateral fixa durante a rolagem no desktop e navegação inferior preservada no mobile. O slogan abaixo da logo foi retirado.
- **Deploy:** apenas frontend (Cloudflare Pages). **Backend do Render e banco Neon não precisam ser modificados** nesta versão. Execute `npm ci`, `npm test`, `npm run build` e depois publique o frontend.
- **API:** fluxos de cadastro, confirmação e idempotência da versão 10 não foram alterados.


## Atualização 10 (correção de mensagens e busca no PDV)

- Nenhuma consulta de comprovante após um POST bem-sucedido: HTTP 2xx é sucesso.
- Avisos genéricos de API e exceções sem resposta HTTP não geram pop-ups de erro na operação. As consultas de reconciliação seguem silenciosas; **ausência de erro não significa confirmação de gravação**. O formulário permanece intacto se não houver confirmação.
- Só mensagens de validação/permissão claras devolvidas pelo servidor (4xx com corpo legível) aparecem na tela. Falhas de transporte/5xx ficam no console para suporte técnico.
- Se a conexão se perder, a tentativa manual da mesma operação mantém a Idempotency-Key, evitando duplicação.
- O seletor do PDV agora é um painel expansível dentro do formulário, sem flutuar sobre a lista de itens. Borda única de foco, botão para limpar e lista alfabética responsiva.
- Publicar somente `frontend` no Cloudflare Pages; backend e banco não mudaram nesta atualização. Na versão 10, verificar **Versão 10** no rodapé após deploy e recarregamento.

## Atualização 09 — confirmação simples de gravações (01/11/2026)

- O aplicativo aceita o **status HTTP 2xx** (incluindo `201 Created`) como sucesso do cadastro, sem consulta adicional a `operations/<chave>/`.
- Foram removidos o polling de confirmação, a tentativa automática de repetir `POST` e o banner de operação pendente.
- Se a conexão cair antes de o navegador receber a resposta, **não aparece erro genérico** nem se afirma que a gravação ocorreu. As listas são recarregadas normalmente; caso o usuário clique de novo com os mesmos dados, a **mesma chave de idempotência** é reutilizada para impedir duplicações no servidor.
- **Erros reais de validação e autenticação continuam visíveis.** Não foi removida a API nem a proteção do backend contra vendas duplicadas.
- Publicação: **atualizar somente o frontend no Cloudflare Pages**. Confirme que a barra lateral indica **Versão 09**; caso apareça outra versão, o deploy antigo ainda está aberto.

## Atualização 08 — ranking em rosca e avisos de conexão (01/11/2026)

- **Itens mais vendidos:** visualização fixa em rosca, sem seletor de tipo nem barra horizontal. Os demais gráficos conservam seus controles.
- **Consultas automáticas e gráficos:** oscilações temporárias da API não produzem toasts vermelhos repetidos. Os dados anteriormente carregados permanecem disponíveis e a sincronização continua sendo tentada.
- **Operações com resposta não confirmada:** em vez de afirmar sucesso ou exibir erro genérico de conexão, aparece um aviso discreto e persistente para o usuário conferir o histórico antes de repetir a ação. Falhas reais de validação continuam visíveis.
- **Relatórios e exportações:** mensagens de erro específicas e botão de nova tentativa quando aplicável; não se mascara uma exportação que falhou.
- Esta versão modifica apenas o frontend. Se o Render já estiver na versão 06/07, não é necessário migrar o banco para esta atualização.

## Atualização 07 — correção do aviso falso após HTTP 201 (31/10/2026)

**Situação corrigida:** ao cadastrar categorias, produtos, vendas ou movimentos, o servidor podia retornar `201 Created` mas o frontend exibia “Não foi possível confirmar a operação”. O tratamento anterior também considerava exceções locais do JavaScript como se fossem erros da API.

- `isTransientFailure` agora reconhece somente falhas do Axios (timeout, rede, 502/503/504); erros de renderização/atualização da interface não são mais classificados como falha de rede.
- Um `201 Created` confirma a gravação. Se a atualização local falhar *depois do sucesso*, a interface avisa apenas que a operação foi salva e recarrega a lista, sem indicar que a API falhou.
- Em timeout real sem confirmação, **não há mais popup vermelho de operação incerta**. A chave idempotente é preservada; a confirmação continua sendo consultada em segundo plano, sem reenviar o POST nessa fase. Se encontrada, a lista e os gráficos são atualizados e o feedback de sucesso é exibido.
- Erros reais de API, como validação inválida (`400`), autenticação (`401`) e conflito (`409`), continuam visíveis ao usuário.
- Os formulários são limpos após confirmação somente se não tiverem sido modificados enquanto a confirmação estava pendente.

### Publicação da versão 07

**Se a versão 06 já está publicada no backend Render, publique somente o frontend Cloudflare Pages atualizado.** Não há alteração de modelos nem migrações do banco nesta versão. O backend precisa conter o endpoint de confirmação `/api/operations/<chave>/` introduzido na versão 06. Execute `npm ci && npm run build` em `frontend/` no deploy e faça recarregamento completo no navegador após a publicação para descartar JavaScript antigo.

**Verificação local:** 51 testes de frontend passaram, incluindo simulações de `201 Created`, perda de resposta HTTP, preservação da chave da operação e erro local após salvar. Sintaxe JavaScript validada. Não foi possível executar o build Vite nesta máquina por falta de dependências `node_modules` ou testar o sistema online no Render/Cloudflare.

## Atualização 06 — confirmação de operações, estorno e gráficos (31/10/2026)

- **Confirmação pós-timeout:** o frontend consulta `GET /api/operations/<chave>/` para recuperar o resultado já registrado pelo backend. A mesma chave idempotente é preservada na sessão, mesmo após recarregar a página, sem armazenar dados de venda no navegador. Repetições de cadastros/vendas não devem duplicar estoque ou receita.
- **Gráficos/tabelas atualizados:** depois de uma venda ou estorno, o sistema invalida e atualiza dashboard, relatórios, posição de estoque e histórico. As consultas GET usam marcador de atualização para não depender de cache de navegador/proxy. Há sincronização periódica quando a tela está visível (20 segundos para dashboard e vendas); não atualiza na aba em segundo plano.
- **Estorno integral:** botão **Estornar** no histórico de vendas, com confirmação e motivo. A API `POST /api/sales/<id>/cancel/` devolve estoque aos lotes de origem (incluindo preservação de validade), grava movimentações inversas, marca a venda cancelada sem apagá-la e remove essa receita dos relatórios e gráficos. Repetir o cancelamento não duplica a devolução.
- **Reembolso:** o valor integral líquido da venda, já descontados os descontos concedidos, é registrado como `refunded_amount`. **Não há integração de pagamento; o dinheiro precisa ser devolvido ao cliente manualmente** (maquininha, Pix, dinheiro, etc.). O app deixa isso explícito na confirmação. Estornos parciais não estão disponíveis nesta versão.
- **UI:** seleção de produto sem linha que muda a altura do formulário, alinhamento responsivo pela largura real do cartão, ícone de seleção no campo e avisos transitórios para falhas de atualização dos gráficos.

### Publicação obrigatória da atualização 06

1. **Faça backup do banco PostgreSQL Neon** antes de atualizar. Preserve a configuração e os dados reais; nunca execute `seed_demo` em produção.
2. Publique **primeiro o backend no Render**. A migração `core.0006_sale_reversal` adiciona os campos de estorno; `build.sh` executa `manage.py migrate --noinput` no deploy. Confirme que a API online está saudável e que a migração terminou sem erro.
3. Publique **depois o frontend no Cloudflare Pages**, mantendo a variável `VITE_API_URL` e o domínio permitido em `CORS_ALLOWED_ORIGINS`. Se o Cloudflare mantiver arquivos JS antigos, faça um novo deploy/limpeza de cache dos assets.
4. Teste uma venda pequena: confirme que aparece imediatamente no histórico, nos indicadores e nos gráficos; faça o estorno, verifique saldo/lotes, histórico e que os valores deixaram de contar em relatórios. O estado **Estornada** permanece visível para auditoria.
5. O Render Free pode suspender o serviço quando não há acesso, ainda sujeito a atraso no primeiro acesso. O código melhora a recuperação da operação, mas não elimina o cold start do host.

**Testes executados neste ambiente:** 47 testes do frontend passaram, além de verificação de sintaxe Python. Os testes de integração Django foram adicionados mas não puderam ser executados aqui, pois não havia dependências Django nem acesso à rede para instalá-las. O deploy online também não foi realizado.

## Atualização 05 — conectividade, gráficos e celular (31/10/2026)

- **Logo horizontal** na conexão e no login, mantendo os SVGs oficiais.
- **POST idempotente** para produtos, categorias, vendas e ajustes de estoque. Se o navegador perder a resposta, a mesma operação pode ser reconsultada/repetida com a chave sem cadastrar ou baixar novamente. O banco guarda a resposta de cada POST com chave.
- **Render Free**: leitura de rede com nova tentativa somente nos GETs, tempo de espera mais tolerante ao início do servidor e mensagem durante a ativação. Não há como eliminar o modo de suspensão gratuita por código.
- **Carregamento seletivo**: histórico, estoque consolidado e outros recursos são buscados ao abrir a tela correspondente. Consultas antigas não substituem cadastros novos.
- **Gráficos**: atualização ao usar a tela, após vendas e em intervalos de 45 segundos enquanto a aba está visível, atualização manual, cache de 30 segundos, cancelamento de consultas ultrapassadas e manutenção dos dados anteriores se houver erro.
- **Desempenho Django**: cálculo dos lotes uma vez por produto serializado, menos leituras repetidas no dashboard, relatório financeiro com filtro de data indexado, Gunicorn com duas threads.
- **Celular**: barra inferior fixa de 5 abas, botões e formulários adequados ao toque, gráficos com rolagem horizontal, modais adaptados e respeito à área segura do aparelho.

### Ordem correta para implantar

1. **Faça backup do PostgreSQL Neon antes de migrar.** Não substitua, apague ou execute `seed_demo` no banco real.
2. Publique **primeiro o backend no Render** a partir deste código. O `backend/build.sh` executará automaticamente `python manage.py migrate --noinput`, criando `core_idempotencyrecord` e o índice de data das vendas. Verifique o status de deploy e `/api/health/`.
3. Publique **depois o frontend no Cloudflare Pages** (build `npm ci && npm run build`, diretório `frontend/dist` e variável `VITE_API_URL=https://SEU-SERVICO.onrender.com/api/`). Mantenha `CORS_ALLOWED_ORIGINS` do Render apontando para o domínio real do frontend.
4. Abra uma sessão e teste um cadastro, uma venda e uma movimentação; valide os gráficos e a navegação no celular.

**Atenção:** hospedar apenas os arquivos novos do frontend, sem migrar e atualizar a API, não ativa a proteção contra duplicidade. O Render Free dorme após 15 minutos sem tráfego e pode demorar cerca de um minuto para iniciar. Uma instância paga elimina a suspensão por inatividade; otimizações de frontend não mudam essa limitação da hospedagem.

## Destaques da versão anterior — Iteração 04 (30/10/2026)

- Identidade visual com variações oficiais SVG: logo vertical compacta no desktop, horizontal no celular, favicon só com símbolo e rodapé com créditos e ano automático.
- Avisos de sucesso e erro em **toast flutuante de 2 segundos**, sem mensagens permanentes ocupando a tela.
- Venda com **adicionador fixo acima do carrinho**; pesquisa e catálogo alfabético exibido ao focar.
- Visão geral com filtros gerenciais de 7/30/90 dias ou 12 meses, escolha de agrupamento e gráficos SVG em barras, linhas, área e rosca, com rankings de produtos e categorias.
- Produtos perecíveis com validade por lote no recebimento, baixa FEFO e separação de saldos físico, vendável e vencido.
- Justificativas predefinidas de estoque e campo livre para outros motivos.
- Busca por nome/SKU diretamente em cada item do carrinho de venda.
- Nova tela **Ver estoque**: saldos, nível mínimo, situação, valor das mercadorias a custo, filtros por nome, categoria e status.
- **Movimentações** separadas da posição de estoque, com justificativa e histórico.
- Pop-ups de estoque crítico, vencidos e próximos de vencer, abertos a partir do dashboard.
- Pop-up de relatórios com intervalo, categorias e itens vendidos; indicadores financeiros, ranking e visão por dia.
- Exportação de estoque e financeiro em **Excel XLSX** com múltiplas abas, formatação, filtros e cabeçalhos.
- Seed idempotente com 33 itens de loja de variedades (potes, vasilhas, bonés, chapéus, carregadores etc.).

Para detalhes dos novos lotes, gráficos e validação: [Iteração 04](docs/20-iteracao-04-experiencia-lotes-graficos-2026-10-30.md). Para identidade visual: [Iteração 03 — Identidade responsiva e rodapé](docs/19-identidade-responsiva-footer-2026-10-30.md). Para contratos de API e relatórios: [Iteração 02](docs/18-identidade-estoque-relatorios-2026-10-29.md).

**Nota:** receita após descontos não é lucro líquido (despesas e custos ainda não são subtraídos).

## 🌐 Publicação gratuita: Cloudflare Pages + Render + Neon

O projeto agora inclui implantação pública com **login por token, banco PostgreSQL no Neon, Django no Render Free e frontend no Cloudflare Pages**. O modo local segue funcionando com SQLite e sem login (somente para desenvolvimento). O deploy de produção **exige** `DEBUG=False`, banco PostgreSQL e chave secreta.

📋 **Siga a ordem de implantação da Atualização 05 acima.** Os arquivos `render.yaml` e `backend/build.sh` já contêm a configuração de publicação, e o primeiro usuário administrativo é criado automaticamente no primeiro build a partir de variáveis de ambiente do Render (o plano gratuito não oferece terminal remoto).

**Importante:** o PostgreSQL remoto inicia vazio; o banco `backend/db.sqlite3` da instalação local não é migrado automaticamente. Não publique o banco local nem o arquivo `.env` no GitHub. O plano gratuito serve para **protótipo/testes**, sem garantia de disponibilidade ou backups gerenciados.


## Escopo desta primeira versão

A versão inicial já permite:

- cadastrar, editar, listar e excluir produtos;
- controlar estoque, estoque mínimo e validade;
- registrar vendas com múltiplos itens na API **e no carrinho da interface**;
- baixar o estoque automaticamente após uma venda e registrar trilha de auditoria;
- ajustar estoques com justificativa e consultar movimentações;
- desativar produtos sem apagar o histórico de movimentação;
- visualizar faturamento, descontos, ticket médio e quantidade de vendas;
- acompanhar a evolução diária da receita nos últimos 7 dias;
- visualizar produtos mais vendidos;
- identificar produtos com estoque crítico;
- identificar produtos com baixa movimentação;
- identificar produtos próximos do vencimento e produtos já vencidos;
- gerar recomendações iniciais de reposição e promoção.

A parte de CRUD existe principalmente para gerar os dados usados pelo módulo de apoio à decisão.

## Tecnologias

### Backend
- Python
- Django
- Django REST Framework
- SQLite (local) / PostgreSQL no Neon (online)
- Gunicorn / WhiteNoise no Render

### Frontend
- Vue 3
- Vite
- Axios

## Como executar

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
# Windows CMD (recomendado Python 3.12 instalado fora da Microsoft Store):
# py -3.12 -m venv .venv
# .venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

API: `http://127.0.0.1:8000/api/`

> Se você já rodou o seed antigo de supermercado e quer ocultar aqueles itens: `python manage.py seed_demo --retire-legacy` (desativa seis SKUs específicos).
> O seed é idempotente e não modifica produtos existentes ao executar novamente.
> Os comandos acima usam dados de demonstração. Não execute `seed_demo` em uma base de produção.
> Na **produção** (`DEBUG=False`), todas as rotas de negócio requerem login; a interface oferece usuário/senha e salva o token somente na sessão da aba. Localmente (`DEBUG=True`) a autenticação é dispensada apenas para facilitar os testes. Não exponha a versão local diretamente à internet.

### 2. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: `http://localhost:5173` (o Vite encaminha `/api` para `127.0.0.1:8000`).
Se necessário, defina `VITE_API_URL` para uma API externa em um `.env.local` do frontend.

## Testes

```bash
cd backend
python -m pytest
# opcional: testes Django internos (não substituem o pytest)
python manage.py test
```

No frontend (Node.js 22+):

```bash
cd frontend
npm ci
npm test
npm run build
```

**Migração obrigatória:** `python manage.py migrate` aplica as migrações existentes de estoque e agora também cria as confirmações idempotentes e o índice de data das vendas. Faça cópia do banco antes de migrar.
Para controle de lotes, toast e gráficos, consulte [Iteração 04](docs/20-iteracao-04-experiencia-lotes-graficos-2026-10-30.md). Para a identidade responsiva, consulte [Iteração 03](docs/19-identidade-responsiva-footer-2026-10-30.md). Para o inventário de mudanças, testes e pendências, consulte [Iteração 02](docs/18-identidade-estoque-relatorios-2026-10-29.md) e [Melhorias anteriores](docs/17-melhorias-2026-10-29.md).
Consulte também `docs/07-plano-de-testes.md`.

## Equipe

- Arthur Azevêdo

## Documentação

A documentação completa está disponível em [`docs/00-indice.md`](docs/00-indice.md).

Documentos principais do Projeto 01:

- [Documento de Visão](docs/01-visao-do-projeto.md)
- [Product Backlog — User Stories](docs/11-user-stories.md)
- [Plano Geral de Iterações](docs/12-plano-iteracoes.md)
- [Relatório do Estado Atual dos Testes](docs/13-estado-atual-testes.md)
- [Plano da Iteração 1](docs/14-iteracao-01.md)
- [Plano de Teste Geral (PTG)](docs/15-plano-teste-geral.md)
- [Plano de Teste das Iterações 1 e 2 (PTI)](docs/16-plano-teste-iteracoes-01-02.md)

## Gestão financeira (V1.4.0)

O Comercializa agora mostra faturamento, receita após descontos, CMV por custo histórico de venda, lucro bruto, margem, despesas operacionais lançadas, resultado operacional estimado, compras de estoque e investimentos em ativos. O menu **Financeiro** abre os filtros, lançamentos, comparações e a exportação Excel com sete abas. Veja [requisitos, casos de uso, modelo de dados e advertências de precisão](docs/25-gestao-financeira.md). **É necessária a migração `0009_financial_entries` no Neon; faça backup antes de publicar.** Atualize backend no Render antes do frontend no Cloudflare Pages. O resultado NÃO é fluxo de caixa nem lucro líquido contábil.

## Cadastro, descrição e navegação por URL (V1.5.0)

A descrição opcional de até 2.000 caracteres está disponível em criação/edição e nos detalhes. Miniaturas no catálogo e nos detalhes de estoque abrem um visualizador com modos de preenchimento e foto inteira (somente CSS, preserva o JPEG). Visão geral, Vendas, Produtos, Estoque, Movimentações e Financeiro possuem endereços próprios no Cloudflare Pages e mantêm a seção ao recarregar a aba. O cadastro agora libera o botão em `finally` mesmo que ocorra erro de foto/interface, sem repetir `POST` automaticamente. Leia o [documento funcional de navegação e produtos](docs/26-cadastro-descricao-rotas-visualizacao.md).

**Migração obrigatória:** `0010_product_description`. Faça backup no Neon e publique o backend com a migração antes de atualizar o frontend. Todos os produtos existentes recebem descrição vazia, sem modificação do estoque ou histórico.
