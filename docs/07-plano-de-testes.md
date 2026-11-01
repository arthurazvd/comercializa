# Plano de Testes

## 1. Objetivo

Definir como o Comercializa será verificado para garantir que funcionalidades operacionais e recomendações do SAD funcionem de maneira consistente.

## 2. Escopo

Nesta etapa serão testados:
- produtos;
- estoque;
- vendas;
- integridade das transações;
- dashboard;
- regras iniciais do SAD.

## 3. Tipos de teste

### Testes unitários
Validam regras isoladas e cálculos.

### Testes de integração
Validam API, banco de dados e atualização de estoque.

### Testes funcionais
Validam os fluxos do ponto de vista do usuário.

### Testes de aceitação
Validam se o comportamento atende aos requisitos.

### Testes do SAD
Validam se os mesmos dados de entrada geram indicadores, prioridades e justificativas esperadas.

## 4. Casos de teste principais

| ID | Cenário | Resultado esperado |
|---|---|---|
| CT01 | Cadastrar produto válido | Produto salvo |
| CT02 | Editar produto | Dados atualizados |
| CT03 | Excluir produto sem dependência | Produto removido |
| CT04 | Registrar venda com estoque | Venda salva e estoque reduzido |
| CT05 | Vender acima do estoque | Operação recusada |
| CT06 | Produto atinge estoque mínimo | Dashboard marca estoque crítico |
| CT07 | Produto vence em 3 dias | SAD gera alerta de validade |
| CT08 | Produto sem venda em 30 dias | SAD indica baixa movimentação |
| CT09 | Produto com estoque crítico | SAD recomenda reposição |
| CT10 | Venda registrada | Ranking e indicadores podem ser atualizados |

## 5. Critérios de aprovação

- nenhuma venda pode gerar estoque negativo;
- estoque deve ser atualizado na mesma transação da venda;
- recomendações devem possuir justificativa;
- regras do SAD devem produzir resultados determinísticos para os mesmos dados;
- testes automatizados críticos devem passar antes de integrar mudanças.

## 6. Automação atual

Execute:

```bash
cd backend
python manage.py test
```

A primeira suíte cobre:
- criação de produto;
- baixa de estoque;
- bloqueio de estoque insuficiente;
- estoque crítico;
- alerta de validade.

## 7. Testes futuros

- testes E2E do Vue;
- testes de autenticação;
- carga;
- segurança;
- usabilidade com comerciante real;
- validação das recomendações com dados históricos reais.


## Iteração 02 — testes de estoque, filtros e Excel (29/10/2026)

Ver também [docs/18-identidade-estoque-relatorios-2026-10-29.md](18-identidade-estoque-relatorios-2026-10-29.md).

- `backend/tests/test_reports_stock.py`: inventário consolidado, alertas, períodos inválidos, desconto rateado, histórico de preço, filtro por categoria/produto, validação da estrutura `.xlsx` e seed idempotente/auditado. **Escritos, não executados** nesta entrega por ausência das dependências Django.
- `frontend/tests/uiPreferences.test.js`: leitura e persistência do tema, inclusive com armazenamento bloqueado. **3 testes aprovados.**
- `frontend/tests/reportUtils.test.js`: intervalo padrão, serialização de filtros, pesquisa sem distinção de caixa, classificação de validade e estoque mínimo. **5 testes aprovados.**
- `frontend/tests/utils.test.js`: validação do carrinho e utilitários preexistentes. **10 testes aprovados.**
- Teste manual pendente: dois temas, responsividade, fluxo de popup, exportação aberta no Excel, busca do carrinho, teclado e Escape.
- `npm run build` e `pytest` devem ser obrigatórios na CI antes do merge.


## Iteração 03 — identidade responsiva e footer (30/10/2026)

- `frontend/tests/branding.test.js`: testa atualização do copyright no novo ano, caminhos e viewBox das cinco variações SVG, favicon sem wordmark, seleção responsiva da logo e presença do footer.
- Executar: `cd frontend && npm test && npm run build`.
- Inspeção visual manual de desktop/celular, dois temas e favicon conforme checklist em [Iteração 03](19-identidade-responsiva-footer-2026-10-30.md).

## Escopo e execução V1.2.0

- Frontend: `cd frontend && npm ci && npm test && npm run build`. Os testes Node isolam lógica do carrinho, normalização de nomes/limites de imagem, contrato de integração, indicadores, avisos e elementos declarados de UI.
- Backend: `cd backend && pip install -r requirements.txt && pytest`. Os novos testes em `tests/test_product_images.py` verificam upload/download JPEG, nome SKU/ID, substituição, exclusão, limite, assinatura inválida, dimensões, autenticação e exclusão em cascata.
- Integração manual obrigatória: testar em câmera real Android/iOS, foto do dispositivo, troca de tema, sessão autenticada, edição de SKU, perda da conexão entre criar produto e subir foto, migração `0007` e leitura após redeploy/sleep no Render.
- **Não há teste E2E/browser automatizado abrangente nem medição de cobertura por campo.** Cenários de campos cobertos e lacunas estão em `21-matriz-rastreabilidade-campos.md`; não afirmar 100% de cobertura só porque todos os testes executaram.
