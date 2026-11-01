# Matriz de rastreabilidade de campos, funcionalidades e testes — V1.2.0

**Objetivo:** evidenciar quais grupos de campos possuem verificações e quais precisam de testes adicionais. “Automatizado” significa **cobertura de cenários essenciais**, não exaustividade de toda entrada, estado visual ou dispositivo. A auditoria leu o código e a suíte existente, sem aferir percentual de cobertura backend no ambiente atual.

| Tela / campos | Backend ou regra | Testes automatizados existentes | Situação e lacunas |
|---|---|---|---|
| Login, senha, token, sessão | auth/status/login/logout, RequireAuthInProduction | `backend/tests/test_deploy_auth.py`, `frontend/tests/deployment-auth.test.js` | Cenários básicos; E2E de expiração/renovação em produção pendente |
| Categoria: nome | CategorySerializer e CategoryViewSet | `backend/tests/test_models.py`, `test_api.py`, `test_idempotency.py` | Cadastro/unicidade; interface real não testada |
| Produto: nome, SKU, categoria, ativo | ProductSerializer | `backend/tests/test_api.py`, `test_models.py`, `test_stock_lots.py` | CRUD e validação geral; combinação de todos os limites de texto pendente |
| Produto: preço de compra/venda e margem | ProductSerializer, Product.margin | `backend/tests/test_models.py`, `test_api.py`, `frontend/tests/utils.test.js` | Cálculos básicos; arredondamento em extremos pendente |
| Produto: saldo atual e mínimo | ProductSerializer, estoque com transações | `backend/tests/test_stock_lots.py`, `test_acceptance.py`, `frontend/tests/ui-v11.test.js` | Não-negativo e concorrência representativa; E2E em rede lenta pendente |
| Perecível, validade, lotes | serializer e serviços de lote | `backend/tests/test_stock_lots.py`, `test_reports_stock.py` | Fluxos de lote/validade presentes; variação de fusos em UI pendente |
| Foto: arquivo, câmera, galeria, prévia | `normalizeProductPhoto`, ProductThumbnail | `frontend/tests/product-photo-v120.test.js` | Nome/limite/contrato automatizados; câmera física e Canvas real **pendentes** |
| Foto: upload, leitura, substituir, excluir | ProductImage + action `/image/` | `backend/tests/test_product_images.py` | Casos de API criados; suíte Django **não executada neste ambiente** |
| Venda: busca, produto, quantidade, desconto | cart/utils, SaleCreateSerializer | `frontend/tests/cart-merge-v11.test.js`, `utils.test.js`, `backend/tests/test_api.py`, `test_improvements.py` | Duplicação bloqueada, limites; fluxo E2E mobile pendente |
| Estorno: motivo, confirmação, reembolso interno | SaleCancelView e ajustes de lote | `backend/tests/test_sale_reversal.py`, `frontend/tests/reversal-and-refresh.test.js` | Reversão e dupla tentativa; integração com pagamento não existe |
| Movimentação: produto, quantidade, motivo, validade | StockAdjustmentSerializer, StockMovement | `backend/tests/test_stock_lots.py`, `test_improvements.py` | Fluxos principais; E2E de formulário ainda não |
| Dashboard: período, métricas, ranking Top 10, categorias | services, reportUtils e charts | `backend/tests/test_sad.py`, `test_reports_stock.py`, `frontend/tests/charts.test.js`, `ui-v11.test.js` | Regras e props; SVG responsivo em navegador real pendente |
| Relatórios: período, categoria, produto, exportação | reports/export_views | `backend/tests/test_reports_stock.py`, `frontend/tests/reportUtils.test.js` | Validações comuns; importação Excel não faz parte do escopo |
| Tema, sidebar, mobile, scrollbar | CSS e localStorage | `frontend/tests/ui-v11.test.js`, `uiPreferences.test.js` | Contratos estáticos; inspeção visual e acessibilidade real pendentes |
| Toast sucesso/erro: 1,5 s | toastController e animationend | `frontend/tests/toast.test.js`, `product-photo-v120.test.js` | Temporizador simulado; animação real em browser pendente |

## Gates mínimos de liberação

1. Backend: instalar `requirements.txt`; `pytest` completo e `python manage.py makemigrations --check --dry-run` com migração `0007` presente.
2. Frontend: `npm ci`, `npm test`, `npm run build` com sucesso.
3. Browser: criar produto com câmera/galeria e editar, trocar SKU, recarregar e conferir que foto continua; testar remoção, erro de rede e fallback; toast sumindo após 1,5s.
4. Persistência: testar leitura após novo deploy/reinício Render e verificar quota/backup do Neon.
5. Evidenciar eventuais falhas antes do deploy público; não afirmar cobertura total só pelo número de testes.
