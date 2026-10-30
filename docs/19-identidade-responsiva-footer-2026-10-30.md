# Iteração 03 — Identidade visual responsiva e rodapé (30/10/2026)

## Objetivo

Aproveitar corretamente as variações oficiais da marca **Comercializa**, tornando a leitura da identidade mais clara em desktop e celular, sem alterar os módulos comerciais já implementados.

## Alterações implementadas

1. **Favicon**: somente o símbolo do carrinho da arte original; um ícone padrão azul escuro/verde e uma variante branco/verde selecionada no modo escuro do sistema operacional, usando `media="(prefers-color-scheme: dark)"` no `index.html`. A preferência do navegador para o favicon é independente do botão de tema do aplicativo.
2. **Logo no desktop**: versão vertical branca com verde, vetorial e com viewBox ajustado, ampliada na barra lateral. A proporção original é preservada.
3. **Logo em celulares/tablets (até 850 px)**: substituição automática pela versão horizontal branca e verde, mais legível no cabeçalho escuro; slogan secundário oculto apenas nesse layout.
4. **Rodapé**: logotipo horizontal com contraste adequado ao tema atual, linha divisória, crédito **“Desenvolvido por Arthur Azevêdo”** e **“© ANO Comercializa. Todos os direitos reservados.”**
5. **Ano automático**: obtido pelo relógio local e renovado a cada minuto enquanto a página está aberta, inclusive quando muda de ano, sem editar arquivos manualmente.
6. **Responsividade**: rodapé alinhado em duas áreas no desktop e centralizado em coluna no celular. O footer fica após o conteúdo, no fim da tela em páginas curtas.

## Arquivos e geração dos ativos

- Arte original: `assets/brand/LOGO COMERCIALIZA.svg`.
- Gerador sem dependências Python externas: `scripts/generate_brand_assets.py`.
- Ativos extraídos para `frontend/public/`:
  - `logo-comercializa-vertical.svg` — versão branca vertical;
  - `logo-comercializa-horizontal-dark.svg` — versão branca horizontal para superfícies escuras;
  - `logo-comercializa-horizontal-light.svg` — versão azul escuro horizontal para superfícies claras;
  - `favicon-comercializa.svg` — símbolo azul escuro/verde para abas claras;
  - `favicon-comercializa-dark.svg` — símbolo branco/verde para abas escuras.

A arte original já continha as variações em grupos vetoriais posicionados além da prancheta padrão. A extração **não redesenha a marca**: seleciona as partes correspondentes e ajusta os `viewBox`, mantendo traçados, gradientes e transparência. Para regenerar na raiz:

```bash
python scripts/generate_brand_assets.py
```

`frontend/src/branding.js` centraliza caminhos e cálculo do ano. Alterações de layout ficam em `frontend/src/App.vue` e `frontend/src/style.css`. A referência antiga `/logo-comercializa.svg` foi mantida para compatibilidade, mas não é mais utilizada pela UI.

## Validação e testes

Teste automatizado adicionado: `frontend/tests/branding.test.js`. Cobertura de:

- mudança de ano (2026 → 2027);
- presença das cinco variações e validade de viewBox;
- favicon somente com símbolo, sem nome em texto ou imagem incorporada;
- orientação retrato/paisagem conforme aplicação;
- associação de favicon, logos e rodapé no HTML/Vue/CSS.

Comandos na pasta `frontend`:

```bash
npm ci
npm test
npm run build
```

### Checklist visual manual

- Desktop (largura > 850 px): logo vertical ampliada na lateral, sem recorte ou distorção.
- Celular (largura <= 850 px): logo horizontal branca no cabeçalho; menus continuam roláveis.
- Tema claro: rodapé com logo azul escuro/verde; tema escuro: rodapé com logo branca/verde.
- Janela estreita (320 px): sem rolagem horizontal causada por logo ou rodapé.
- Favicon: apenas o símbolo; para ver atualização, recarregar a aba (alguns navegadores mantêm cache do favicon).
- Rodapé: nome Arthur Azevêdo com acento; ano atual obtido automaticamente.

## Limites e notas

- A atualização do ano verifica o relógio a cada 60 segundos. Não altera exercícios fiscais, lançamentos nem relatórios.
- Favicon segue a preferência de cor do **navegador/sistema**, enquanto o rodapé acompanha o **tema do próprio aplicativo**.
- Nenhuma API, seed, migração ou configuração do banco de dados foi alterada nesta iteração.

## Resultado da validação neste pacote

- `npm test`: **23 testes aprovados**, incluindo 5 de branding (30/10/2026).
- SVGs: renderizados individualmente, sem recortes e com transparência.
- `npm run build`: **não concluído** neste ambiente; `npm ci` não conseguiu terminar a instalação dos pacotes. No computador com Node.js e rede, executar `npm ci`, `npm test` e `npm run build`.
- Teste visual do app em navegador: **pendente**, pois a navegação automatizada foi bloqueada no ambiente.
