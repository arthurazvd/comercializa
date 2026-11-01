// Rotas estáveis por página. Sem dependência extra de roteador.
export const TAB_PATHS = Object.freeze({
  dashboard: '/visao-geral', sales: '/vendas', products: '/produtos',
  inventory: '/estoque', movements: '/movimentacoes',
})
export const FINANCE_PATH = '/financeiro'
const pathTab = Object.fromEntries(Object.entries(TAB_PATHS).map(([tab, path]) => [path, tab]))
export function normalizePath(path) {
  const clean = String(path || '/').split(/[?#]/, 1)[0].replace(/\/+$/, '')
  return clean || '/'
}
export function tabFromPath(path) {
  return pathTab[normalizePath(path)] || 'dashboard'
}
export function pathForTab(tab) {
  return TAB_PATHS[tab] || TAB_PATHS.dashboard
}
export function isKnownPagePath(path) {
  return Object.hasOwn(pathTab, normalizePath(path)) || normalizePath(path) === FINANCE_PATH
}
export function isFinancePath(path) {
  return normalizePath(path) === FINANCE_PATH
}
