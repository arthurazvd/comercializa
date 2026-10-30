<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, getAuthToken, saveAuthToken, clearAuthToken } from './api'
import AppIcon from './components/AppIcon.vue'
import DecisionChart from './components/DecisionChart.vue'
import { sortedSaleOptions, MOVEMENT_REASONS, movementNote, periodDates, aggregateDaily, productChartData, concentrationPercentage } from './charts'
import { createToastController } from './toast'
import { formatMoney, localDateISO, eligibleProducts, calculateCart, validCart } from './utils'
import { defaultReportFilters, queryReport, filteredInventory, matchProductSearch, inventoryStatus } from './reportUtils'
import { readTheme, saveTheme } from './uiPreferences'
import { BRAND_ASSETS, getCopyrightYear } from './branding'

// A interface só carrega dados após verificar a sessão. Produção exige login.
const authChecking = ref(true)
const authRequired = ref(true)
const authenticated = ref(false)
const authUsername = ref('')
const authStartupError = ref('')
const loginBusy = ref(false)
const loginForm = ref({ username: '', password: '' })
const loginError = ref('')
const tab = ref('dashboard')
const products = ref([])
const categories = ref([])
const dashboard = ref(null)
const sales = ref([])
const movements = ref([])
const stockOverview = ref(null)
const finance = ref(null)
const modal = ref('')
const theme = ref(readTheme())
const copyrightYear = ref(getCopyrightYear())
let yearRefreshInterval
const toast = ref(null)
const toastController = createToastController(value => { toast.value = value })
const busy = ref(false)
const loading = ref(true)
const financeLoading = ref(false)
const search = ref('')
const filter = ref('all')
const stockSearch = ref('')
const stockFilter = ref('all')
const stockCategory = ref('')
const movementProduct = ref('')
const stockReason = ref('recebimento')
const stockCustomNote = ref('')
const stockExpiry = ref('')
const stockNote = computed(() => movementNote(stockReason.value, stockCustomNote.value))
const stockProduct = ref('')
const stockDelta = ref(1)
const categoryName = ref('')
const reportFilters = ref(defaultReportFilters())
const blankProduct = () => ({ perishable: false, id: null, name: '', category: '', sku: '', purchase_price: 0, sale_price: 0, stock: 0, minimum_stock: 0, expiration_date: '', active: true })
const productForm = ref(blankProduct())
const saleForm = ref({ items: [], discount: 0 })
const saleDraft = ref({ product: '', quantity: 1, query: '' })
const saleSearchOpen = ref(false)
const saleSearchInput = ref(null)
let saleSearchBlurTimer = null
let cartItemSequence = 0
const chartPeriod = ref('30d')
const chartGrouping = ref('day')
const chartStyle = ref('bar')
const productChartStyle = ref('bar')
const categoryChartStyle = ref('donut')
const chartMetric = ref('revenue')
const dashboardReport = ref(null)
const chartLoading = ref(false)
const chartError = ref(false)
let dashboardChartRequest = 0
const today = localDateISO()
const money = formatMoney
const saleChoices = computed(() => sortedSaleOptions(products.value, saleDraft.value.query))
const selectedMovementProduct = computed(() => products.value.find(p => p.id === Number(stockProduct.value)))
const showingReceiptExpiry = computed(() => Number(stockDelta.value) > 0 && Boolean(selectedMovementProduct.value?.perishable))
const movementDirectionValid = computed(() => {
  const choice = MOVEMENT_REASONS.find(r => r.value === stockReason.value)
  return Boolean(choice) && (choice.direction === 'both' || (Number(stockDelta.value) > 0 ? choice.direction === 'in' : choice.direction === 'out'))
})
const movementFormValid = computed(() => Number.isInteger(Number(stockDelta.value)) && Number(stockDelta.value) !== 0 && !!stockProduct.value && !!stockNote.value && movementDirectionValid.value && (!showingReceiptExpiry.value || !!stockExpiry.value))
const trendRows = computed(() => aggregateDaily(dashboardReport.value?.daily || [], chartGrouping.value, chartMetric.value === 'revenue' ? 'revenue' : 'quantity'))
const rankedRows = computed(() => productChartData(dashboardReport.value?.products || [], chartMetric.value === 'revenue' ? 'revenue' : 'quantity'))
const categoryRows = computed(() => productChartData(dashboardReport.value?.categories || [], chartMetric.value === 'revenue' ? 'revenue' : 'quantity'))
const summaryInsights = computed(() => ({
  units: dashboardReport.value?.summary?.items_sold || 0,
  activeItems: (dashboardReport.value?.products || []).length,
  concentration: concentrationPercentage(dashboardReport.value?.categories || []),
  topCategory: dashboardReport.value?.categories?.[0]?.name || '—',
}))
const visibleProducts = computed(() => products.value.filter(p => matchProductSearch(p, search.value) && (
  filter.value === 'all' || (filter.value === 'active' && p.active) || (filter.value === 'low' && p.active && Number(p.available_stock ?? p.stock) <= p.minimum_stock) || (filter.value === 'inactive' && !p.active))))
const inventoryProducts = computed(() => filteredInventory(products.value, stockSearch.value, stockFilter.value, stockCategory.value))
const filteredMovements = computed(() => movements.value.filter(m => !movementProduct.value || String(m.product) === String(movementProduct.value)))
const inventoryCount = computed(() => ({
  all: products.value.filter(p => p.active).length,
  critico: products.value.filter(p => p.active && Number(p.available_stock ?? p.stock) <= p.minimum_stock).length,
  vencido: products.value.filter(p => inventoryStatus(p, today) === 'vencido').length,
  a_vencer: products.value.filter(p => inventoryStatus(p, today) === 'a_vencer').length,
}))
const subtotal = computed(() => calculateCart(saleForm.value.items, products.value).subtotal)
const total = computed(() => calculateCart(saleForm.value.items, products.value, saleForm.value.discount).total)
const cartValid = computed(() => validCart(saleForm.value.items, products.value, saleForm.value.discount, today))
const modalItems = computed(() => {
  if (modal.value === 'critico') return filteredInventory(products.value, '', 'critico')
  if (modal.value === 'vencido' || modal.value === 'a_vencer') return filteredInventory(products.value, '', modal.value)
  return []
})
const modalTitles = { critico: 'Produtos em estoque crítico', vencido: 'Produtos vencidos', a_vencer: 'Próximos do vencimento', finance: 'Análise financeira e vendas' }

watch(theme, value => { document.documentElement.dataset.theme = value; saveTheme(value) }, { immediate: true })
watch(modal, value => { document.body.style.overflow = value ? 'hidden' : '' })
watch(() => reportFilters.value.category, () => { reportFilters.value.product = '' })
watch(chartPeriod, period => { if (period === '90d') chartGrouping.value = 'week'; else if (period === '12m') chartGrouping.value = 'month'; else chartGrouping.value = 'day'; refreshDashboardCharts() })
watch(stockProduct, () => { stockExpiry.value = '' })
watch(stockDelta, value => { if (Number(value) <= 0) { stockExpiry.value = ''; if (stockReason.value === 'recebimento' || stockReason.value === 'devolucao') stockReason.value = 'avaria' } else if (stockReason.value === 'avaria' || stockReason.value === 'perda') stockReason.value = 'recebimento' })
function onKeydown(event) { if (event.key === 'Escape') closeModal() }
onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  yearRefreshInterval = window.setInterval(() => { copyrightYear.value = getCopyrightYear() }, 60_000)
  window.addEventListener('comercializa:unauthorized', onUnauthorized)
  initializeSession()
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('comercializa:unauthorized', onUnauthorized)
  window.clearInterval(yearRefreshInterval)
  toastController.dispose()
  window.clearTimeout(saleSearchBlurTimer)
  document.body.style.overflow = ''
})
function onUnauthorized() {
  if (!authRequired.value) return
  authenticated.value = false
  authUsername.value = ''
  dashboard.value = null
  products.value = []
  categories.value = []
  sales.value = []
  movements.value = []
  loginError.value = 'Sua sessão expirou ou foi encerrada. Entre novamente.'
}
async function initializeSession() {
  authChecking.value = true
  authStartupError.value = ''
  try {
    const { data } = await api.get('auth/status/')
    authRequired.value = Boolean(data.authentication_required)
    authenticated.value = !authRequired.value || Boolean(data.authenticated)
    authUsername.value = data.username || ''
    if (authenticated.value) {
      await loadAll()
      refreshDashboardCharts()
    } else if (getAuthToken()) {
      clearAuthToken()
    }
  } catch (error) {
    authRequired.value = true
    authenticated.value = false
    if (error?.response?.status === 401) {
      clearAuthToken()
      loginError.value = 'Sua sessão expirou. Entre novamente.'
    } else {
      authStartupError.value = 'Não foi possível conectar ao servidor. Confira o endereço da API e tente novamente.'
    }
  } finally { authChecking.value = false }
}
async function signIn() {
  if (loginBusy.value) return
  loginBusy.value = true
  loginError.value = ''
  try {
    const { data } = await api.post('auth/login/', {
      username: loginForm.value.username.trim(),
      password: loginForm.value.password,
    })
    if (!data.token) throw new Error('O servidor não retornou um token válido.')
    saveAuthToken(data.token)
    const session = await api.get('auth/status/')
    if (!session.data.authenticated) throw new Error('Não foi possível confirmar a sessão.')
    authUsername.value = session.data.username || data.username || ''
    authRequired.value = true
    authenticated.value = true
    loginForm.value.password = ''
    authStartupError.value = ''
    await loadAll()
    refreshDashboardCharts()
  } catch (error) {
    clearAuthToken()
    authenticated.value = false
    loginError.value = error.response ? errorText(error) : (error.message || errorText(error))
  } finally { loginBusy.value = false }
}
async function signOut() {
  try { await api.post('auth/logout/') } catch { /* logout local mesmo sem resposta da API */ }
  clearAuthToken()
  onUnauthorized()
  loginError.value = ''
  tab.value = 'dashboard'
  modal.value = ''
  dashboardReport.value = null
}
function alertUser(text, type = 'success') { toastController.show(text, type) }
function errorText(error) {
  const data = error?.response?.data
  if (!data) return 'Não foi possível conectar à API. Verifique se o backend está ativo.'
  if (typeof data === 'string') return data
  if (data.detail) return String(data.detail)
  return Object.entries(data).map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : value}`).join(' · ')
}
async function loadAll() {
  loading.value = true
  try {
    const [p, c, d, s, m, st] = await Promise.all([
      api.get('products/'), api.get('categories/'), api.get('dashboard/'), api.get('sales/'), api.get('stock-movements/'), api.get('stock-overview/'),
    ])
    products.value = p.data; categories.value = c.data; dashboard.value = d.data
    sales.value = s.data; movements.value = m.data; stockOverview.value = st.data
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { loading.value = false }
}
function resetProduct() { productForm.value = blankProduct() }
function editProduct(product) { productForm.value = { ...product, category: product.category ?? '', expiration_date: product.expiration_date ?? '' }; tab.value = 'products'; window.scrollTo({ top: 0, behavior: 'smooth' }) }
async function saveProduct() {
  if (busy.value) return
  busy.value = true
  try {
    const payload = { ...productForm.value, category: productForm.value.category || null, sku: productForm.value.sku || null, expiration_date: productForm.value.expiration_date || null }
    if (payload.id) await api.put(`products/${payload.id}/`, payload)
    else await api.post('products/', payload)
    alertUser(payload.id ? 'Produto atualizado com sucesso.' : 'Produto cadastrado com sucesso.')
    resetProduct(); await loadAll()
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function toggleProduct(product) {
  if (busy.value) return
  busy.value = true
  try { await api.patch(`products/${product.id}/`, { active: !product.active }); await loadAll(); alertUser('Situação do produto atualizada.') }
  catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function deleteProduct(product) {
  if (!confirm(`Excluir "${product.name}"? Produtos com histórico devem ser desativados.`)) return
  try { await api.delete(`products/${product.id}/`); await loadAll(); alertUser('Produto excluído.') }
  catch (error) { alertUser(errorText(error), 'error') }
}
async function addCategory() {
  if (!categoryName.value.trim()) return
  try { await api.post('categories/', { name: categoryName.value.trim() }); categoryName.value = ''; await loadAll(); alertUser('Categoria criada.') }
  catch (error) { alertUser(errorText(error), 'error') }
}
function addItem() {
  if (!saleDraft.value.product || !Number.isInteger(Number(saleDraft.value.quantity)) || Number(saleDraft.value.quantity) < 1) return
  const p = products.value.find(p => p.id === Number(saleDraft.value.product))
  if (!p || saleForm.value.items.some(i => Number(i.product) === p.id) || Number(saleDraft.value.quantity) > Number(p.available_stock ?? p.stock)) {
    alertUser('Produto já adicionado ou quantidade indisponível.', 'error')
    return
  }
  saleForm.value.items.push({ product: p.id, quantity: Number(saleDraft.value.quantity), key: ++cartItemSequence })
  saleDraft.value = { product: '', quantity: 1, query: '' }
  saleSearchOpen.value = false
  nextTick(() => saleSearchInput.value?.focus())
}
function removeItem(i) { saleForm.value.items.splice(i, 1) }
function chooseSaleItem(p) { window.clearTimeout(saleSearchBlurTimer); saleDraft.value.product = p.id; saleDraft.value.query = p.name; saleSearchOpen.value = false }
function showSaleOptions() { window.clearTimeout(saleSearchBlurTimer); saleSearchOpen.value = true }
function onSaleInput() { saleDraft.value.product = ''; saleSearchOpen.value = true }
function hideSaleOptions() { window.clearTimeout(saleSearchBlurTimer); saleSearchBlurTimer = window.setTimeout(() => { saleSearchOpen.value = false }, 120) }
async function refreshDashboardCharts() {
  const requestId = ++dashboardChartRequest
  chartLoading.value = true
  chartError.value = false
  try {
    const dates = periodDates(chartPeriod.value, localDateISO())
    const result = await api.get(`reports/finance/?${queryReport(dates)}`)
    if (requestId === dashboardChartRequest) dashboardReport.value = result.data
  } catch (error) { if (requestId === dashboardChartRequest) { chartError.value = true; alertUser(errorText(error), 'error') } }
  finally { if (requestId === dashboardChartRequest) chartLoading.value = false }
}
async function registerSale() {
  if (!cartValid.value || busy.value) return
  busy.value = true
  try {
    await api.post('sales/', { discount: Number(saleForm.value.discount) || 0, items: saleForm.value.items.map(i => ({ product: Number(i.product), quantity: Number(i.quantity) })) })
    saleForm.value = { items: [], discount: 0 }
    saleDraft.value = { product: '', quantity: 1, query: '' }
    await Promise.all([loadAll(), refreshDashboardCharts()]); alertUser('Venda registrada! Estoque atualizado automaticamente.')
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function adjustStock() {
  if (busy.value || !movementFormValid.value) return
  busy.value = true
  try {
    await api.post('stock-movements/', { product: Number(stockProduct.value), delta: Number(stockDelta.value), note: stockNote.value, justification: stockReason.value, ...(showingReceiptExpiry.value ? { expiration_date: stockExpiry.value } : {}) })
    stockDelta.value = 1; stockReason.value = 'recebimento'; stockCustomNote.value = ''; stockExpiry.value = ''; await loadAll(); alertUser('Movimentação registrada.')
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
function openModal(type) { modal.value = type; if (type === 'finance') refreshFinance() }
function closeModal() { modal.value = '' }
function openInventory(status = 'all') { tab.value = 'inventory'; stockFilter.value = status; closeModal() }
async function refreshFinance() {
  if (!reportFilters.value.start || !reportFilters.value.end || reportFilters.value.start > reportFilters.value.end) { alertUser('Corrija o intervalo de datas.', 'error'); return }
  financeLoading.value = true
  try { finance.value = (await api.get(`reports/finance/?${queryReport(reportFilters.value)}`)).data }
  catch (error) { alertUser(errorText(error), 'error') }
  finally { financeLoading.value = false }
}
async function exportXlsx(type) {
  try {
    const url = type === 'stock' ? 'stock-export/' : `reports/finance/export/?${queryReport(reportFilters.value)}`
    const response = await api.get(url, { responseType: 'blob', timeout: 60000 })
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a'); const urlObject = URL.createObjectURL(blob)
    link.href = urlObject; link.download = type === 'stock' ? 'comercializa_estoque.xlsx' : 'comercializa_financeiro.xlsx'
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(urlObject), 1200)
  } catch (error) { alertUser(errorText(error), 'error') }
}
function shortDate(value) { return value ? `${value.substring(8, 10)}/${value.substring(5, 7)}/${value.substring(0, 4)}` : '—' }
function dateTime(value) { return value ? new Date(value).toLocaleString('pt-BR') : '—' }
function labelStatus(p) {
  return { normal: 'Em dia', critico: 'Crítico', vencido: 'Vencido', a_vencer: 'A vencer', inativo: 'Inativo' }[inventoryStatus(p, today)]
}
</script>

<template>
<section v-if="authChecking || (authRequired && !authenticated)" class="auth-page">
  <div class="auth-card">
    <img src="/logo-comercializa-vertical.svg" alt="Comercializa" class="auth-logo" />
    <template v-if="authChecking">
      <h1>Conectando ao Comercializa…</h1>
      <p>Verificando o acesso ao sistema.</p>
    </template>
    <template v-else>
      <span class="eyebrow">ACESSO SEGURO</span>
      <h1>Entrar no Comercializa<span class="title-accent">.</span></h1>
      <p>Use o usuário e a senha cadastrados para acessar vendas, produtos e estoque.</p>
      <div v-if="authStartupError" class="auth-error" role="alert">{{ authStartupError }} <button type="button" @click="initializeSession">Tentar conexão</button></div>
      <form class="auth-form" @submit.prevent="signIn">
        <label>Usuário<input v-model="loginForm.username" name="username" autocomplete="username" required autofocus placeholder="Seu usuário" /></label>
        <label>Senha<input v-model="loginForm.password" name="password" type="password" autocomplete="current-password" required placeholder="Sua senha" /></label>
        <div v-if="loginError" class="auth-error" role="alert">{{ loginError }}</div>
        <button type="submit" class="btn primary" :disabled="loginBusy">{{ loginBusy ? 'Entrando…' : 'Entrar no sistema' }}</button>
      </form>
    </template>
    <small class="auth-note">Seus dados ficam no banco de dados do sistema, não no navegador.</small>
  </div>
</section>
<div v-else class="layout">
  <aside class="sidebar">
    <div class="brand">
      <img :src="BRAND_ASSETS.verticalOnDark" alt="Comercializa" class="brand-logo brand-logo-vertical" width="110" height="151" />
      <img :src="BRAND_ASSETS.horizontalOnDark" alt="Comercializa" class="brand-logo brand-logo-horizontal" width="225" height="42" />
      <div class="brand-subtitle">SEU NEGÓCIO EM MOVIMENTO</div>
    </div>
    <div class="sidebar-label">MENU PRINCIPAL</div>
    <nav aria-label="Navegação principal">
      <button :class="{ active: tab === 'dashboard' }" @click="tab = 'dashboard'"><AppIcon name="dashboard" /> Visão geral</button>
      <button :class="{ active: tab === 'sales' }" @click="tab = 'sales'"><AppIcon name="cart" /> Vendas</button>
      <button :class="{ active: tab === 'products' }" @click="tab = 'products'"><AppIcon name="products" /> Produtos</button>
      <button :class="{ active: tab === 'inventory' }" @click="tab = 'inventory'"><AppIcon name="package" /> Ver estoque</button>
      <button :class="{ active: tab === 'movements' }" @click="tab = 'movements'"><AppIcon name="arrows" /> Movimentações</button>
    </nav>
    <div class="sidebar-footer"><div class="sidebar-footer-head"><span class="status-dot"></span> {{ authRequired ? 'Ambiente conectado' : 'Ambiente de desenvolvimento' }}</div><small>Gestão de loja de variedades</small></div>
  </aside>
  <main class="main-content">
    <div class="topbar"><span class="topbar-path">PAINEL <span class="crumb">/ {{ { dashboard: 'Visão geral', sales: 'Vendas', products: 'Produtos', inventory: 'Posição de estoque', movements: 'Movimentações' }[tab] }}</span></span><div class="topbar-actions"><span class="topbar-date">{{ shortDate(today) }}</span><button type="button" class="icon-btn" :title="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'" :aria-label="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'" @click="theme = theme === 'dark' ? 'light' : 'dark'"><AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" /></button><button type="button" class="icon-btn" aria-label="Atualizar dados" title="Atualizar dados" @click="loadAll"><AppIcon name="refresh" /></button><span v-if="authRequired" class="topbar-user">{{ authUsername }}</span><button v-if="authRequired" type="button" class="btn secondary" title="Sair da conta" @click="signOut">Sair</button></div></div>
    <Transition name="toast"><div v-if="toast" :class="['toast-notice', toast.type]" :role="toast.type === 'error' ? 'alert' : 'status'" :aria-live="toast.type === 'error' ? 'assertive' : 'polite'"><span class="toast-glyph"><AppIcon :name="toast.type === 'error' ? 'alert' : 'check'" :size="20" /></span><span>{{ toast.text }}</span><button type="button" aria-label="Dispensar notificação" @click="toastController.dismiss()"><AppIcon name="close" :size="17" /></button><span class="toast-timer"></span></div></Transition>
    <div v-if="loading && !dashboard" class="panel loading">Carregando dados…</div>

    <section v-if="tab === 'dashboard' && dashboard">
      <header class="page-header"><div><span class="eyebrow">DASHBOARD / PERFORMANCE</span><h1>Visão geral<span class="title-accent">.</span></h1><p>Uma visão clara das vendas, do estoque e do que merece atenção.</p></div><button class="btn secondary" @click="openModal('finance')"><AppIcon name="chart" :size="17" /> Explorar relatórios</button></header>
      <div class="cards">
        <button type="button" class="metric metric-click" @click="openModal('finance')"><div class="metric-top"><small>Receita após descontos · 30 dias</small><span class="metric-icon green"><AppIcon name="money" /></span></div><b>{{ money(dashboard.summary.revenue) }}</b><span class="metric-detail">Ver detalhamento financeiro <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('finance')"><div class="metric-top"><small>Vendas realizadas · 30 dias</small><span class="metric-icon blue"><AppIcon name="cart" /></span></div><b>{{ dashboard.summary.sales_count }}</b><span class="metric-detail">Ticket médio {{ money(dashboard.summary.average_ticket) }} <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('critico')"><div class="metric-top"><small>Estoque crítico</small><span class="metric-icon orange"><AppIcon name="alert" /></span></div><b>{{ inventoryCount.critico }}</b><span class="metric-detail">Ver produtos para reposição <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('vencido')"><div class="metric-top"><small>Produtos vencidos</small><span class="metric-icon red"><AppIcon name="clock" /></span></div><b>{{ inventoryCount.vencido }}</b><span class="metric-detail">{{ inventoryCount.a_vencer }} próximos do vencimento <AppIcon name="arrow" :size="14" /></span></button>
      </div>
      <div class="dashboard-chart-toolbar panel">
        <div><span class="eyebrow">ANÁLISE GERENCIAL</span><h2>Explore os dados de vendas</h2><p>Altere período, agrupamento e visualização. Receita considera os descontos, mas não representa lucro.</p></div>
        <div class="chart-controls"><label>Período<select v-model="chartPeriod"><option value="7d">Últimos 7 dias</option><option value="30d">Últimos 30 dias</option><option value="90d">Últimos 90 dias</option><option value="12m">Últimos 12 meses</option></select></label><label>Indicador<select v-model="chartMetric"><option value="revenue">Receita (R$)</option><option value="quantity">Unidades vendidas</option></select></label><label>Agrupar<select v-model="chartGrouping"><option value="day">Por dia</option><option value="week">Por semana</option><option value="month">Por mês</option></select></label><small v-if="chartLoading" class="chart-refreshing">Atualizando gráficos…</small></div>
      </div>
      <div v-if="chartError" class="panel"><p>Não foi possível carregar os gráficos. <button class="btn secondary" @click="refreshDashboardCharts">Tentar novamente</button></p></div>
      <div v-else-if="chartLoading && !dashboardReport" class="panel">Carregando análises…</div>
      <template v-else-if="dashboardReport">
        <div class="insight-strip"><div><span>Unidades vendidas</span><strong>{{ summaryInsights.units }}</strong></div><div><span>Produtos diferentes vendidos</span><strong>{{ summaryInsights.activeItems }}</strong></div><div><span>Maior categoria no faturamento</span><strong>{{ summaryInsights.concentration }}%</strong><small>{{ summaryInsights.topCategory }}</small></div><div><span>Ticket médio do período</span><strong>{{ money(dashboardReport.summary.average_ticket) }}</strong></div></div>
        <div class="grid-2 dashboard-top">
          <article class="panel chart-panel"><div class="panel-heading"><div><span class="eyebrow">SÉRIE TEMPORAL</span><h2>Evolução das vendas</h2></div><select v-model="chartStyle" aria-label="Tipo de gráfico de evolução"><option value="bar">Barras</option><option value="line">Linhas</option><option value="area">Área</option><option value="donut">Rosca (participação)</option></select></div><DecisionChart :rows="trendRows" :type="chartStyle" :currency="chartMetric === 'revenue'" label="Evolução das vendas no período selecionado" /></article>
          <article class="panel chart-panel"><div class="panel-heading"><div><span class="eyebrow">RANKING</span><h2>Itens mais vendidos</h2></div><select v-model="productChartStyle" aria-label="Tipo de gráfico dos mais vendidos"><option value="bar">Barras</option><option value="line">Linhas</option><option value="donut">Rosca</option></select></div><DecisionChart :rows="rankedRows" :type="productChartStyle" :currency="chartMetric === 'revenue'" label="Produtos mais vendidos" /><div class="top-product-list"><div v-for="(p, i) in dashboardReport.products.slice(0, 5)" :key="p.id" class="rank-row"><span class="rank-index">{{ String(i + 1).padStart(2, '0') }}</span><strong>{{ p.name }}</strong><span class="quantity">{{ p.quantity }} un.</span></div></div></article>
        </div>
        <article class="panel chart-panel category-analysis"><div class="panel-heading"><div><span class="eyebrow">MIX COMERCIAL</span><h2>Participação por categoria</h2></div><select v-model="categoryChartStyle" aria-label="Tipo de gráfico por categoria"><option value="donut">Rosca</option><option value="bar">Barras</option><option value="line">Linhas</option></select></div><DecisionChart :rows="categoryRows" :type="categoryChartStyle" :currency="chartMetric === 'revenue'" label="Distribuição das vendas por categoria" /></article>
      </template>
      <div class="grid-2">
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">AÇÃO RECOMENDADA</span><h2>Prioridades do negócio</h2></div><span class="count-pill">{{ dashboard.recommendations.length }} avisos</span></div><div v-if="!dashboard.recommendations.length" class="empty">Nenhuma pendência identificada.</div><div v-for="(r, i) in dashboard.recommendations.slice(0, 6)" :key="i" class="recommendation"><span :class="['priority', r.priority]">{{ r.priority }}</span><div><strong>{{ r.product }}</strong><p>{{ r.message }}</p><small>{{ r.reason }}</small></div></div></article>
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">CONTROLE DE ESTOQUE</span><h2>Acompanhe as situações</h2></div><AppIcon name="package" /></div><button class="overview-link" @click="openModal('critico')"><span class="overview-icon orange"><AppIcon name="alert" /></span><span><strong>Estoque no mínimo</strong><small>Itens com saldo abaixo ou igual ao mínimo</small></span><b>{{ inventoryCount.critico }}</b><AppIcon name="arrow" :size="16" /></button><button class="overview-link" @click="openModal('vencido')"><span class="overview-icon red"><AppIcon name="clock" /></span><span><strong>Itens vencidos</strong><small>Separe apenas as unidades vencidas</small></span><b>{{ inventoryCount.vencido }}</b><AppIcon name="arrow" :size="16" /></button><button class="overview-link" @click="openModal('a_vencer')"><span class="overview-icon blue"><AppIcon name="calendar" /></span><span><strong>Vencem em 15 dias</strong><small>Antecipe as decisões de reposição</small></span><b>{{ inventoryCount.a_vencer }}</b><AppIcon name="arrow" :size="16" /></button><button class="btn secondary full" style="margin-top:18px" @click="openInventory()">Consultar todo o estoque <AppIcon name="arrow" :size="16" /></button></article>
      </div>
    </section>

    <section v-if="tab === 'products'"><header class="page-header"><div><span class="eyebrow">CATÁLOGO / CADASTROS</span><h1>Produtos<span class="title-accent">.</span></h1><p>Cadastre e organize os itens de sua loja.</p></div><span class="header-count">{{ products.length }} itens cadastrados</span></header>
      <div class="grid-form"><div class="stack"><form class="panel" @submit.prevent="saveProduct"><div class="panel-heading"><div><span class="eyebrow">GESTÃO DO CATÁLOGO</span><h2>{{ productForm.id ? 'Editar produto' : 'Cadastrar produto' }}</h2></div><AppIcon name="products" /></div><label>Nome do produto<input v-model="productForm.name" required maxlength="150" placeholder="Ex.: Pote plástico 1 litro" /></label><div class="form-row"><label>Categoria<select v-model="productForm.category"><option value="">Sem categoria</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></label><label>SKU<input v-model="productForm.sku" maxlength="50" placeholder="Opcional" /></label></div><div class="form-row"><label>Preço de compra<input v-model.number="productForm.purchase_price" type="number" step="0.01" min="0" required /></label><label>Preço de venda<input v-model.number="productForm.sale_price" type="number" step="0.01" min="0" required /></label></div><div class="form-row"><label>Saldo inicial / atual<input v-model.number="productForm.stock" type="number" step="1" min="0" required :disabled="Boolean(productForm.id && productForm.perishable)" /><small v-if="productForm.id && productForm.perishable" class="help-text">Para receber mais unidades, vá a Movimentações e informe a validade.</small></label><label>Estoque mínimo<input v-model.number="productForm.minimum_stock" type="number" step="1" min="0" required /></label></div><label class="check-label"><input v-model="productForm.perishable" type="checkbox" /> Produto perecível (controlar validade por lote)</label><label>{{ productForm.perishable ? 'Validade do saldo inicial / legado' : 'Validade (se aplicável)' }}<input v-model="productForm.expiration_date" type="date" :required="productForm.perishable && Number(productForm.stock) > 0 && !productForm.id" /></label><label class="check-label"><input v-model="productForm.active" type="checkbox" /> Produto ativo</label><div class="form-actions"><button class="btn primary" type="submit" :disabled="busy"><AppIcon :name="productForm.id ? 'check' : 'add'" :size="16" />{{ busy ? 'Salvando…' : productForm.id ? 'Salvar alterações' : 'Cadastrar produto' }}</button><button v-if="productForm.id" class="btn secondary" type="button" @click="resetProduct">Cancelar</button></div><p class="help-text">Para entradas e saídas de estoque use Movimentações: cada ajuste fica registrado.</p></form><form class="panel" @submit.prevent="addCategory"><div class="panel-heading"><h2>Nova categoria</h2></div><label>Nome<input v-model="categoryName" maxlength="100" required placeholder="Ex.: Utilidades domésticas" /></label><button type="submit" class="btn secondary"><AppIcon name="add" :size="16" />Adicionar categoria</button></form></div>
      <article class="panel catalog"><div class="panel-heading"><div><span class="eyebrow">PRODUTOS CADASTRADOS</span><h2>Catálogo</h2></div><span class="count-pill">{{ visibleProducts.length }} resultados</span></div><div class="filters"><label class="search-input"><AppIcon name="search" :size="17" /><input v-model="search" type="search" placeholder="Buscar por produto, SKU ou categoria" aria-label="Pesquisar produtos" /></label><select v-model="filter" aria-label="Situação"><option value="all">Todos</option><option value="active">Ativos</option><option value="low">Estoque crítico</option><option value="inactive">Inativos</option></select></div><div v-if="!visibleProducts.length" class="empty">Nenhum produto encontrado.</div><div v-for="p in visibleProducts" :key="p.id" class="catalog-item"><div class="product-avatar"><AppIcon name="package" /></div><div class="product-info"><strong>{{ p.name }}</strong><small>{{ p.category_name || 'Sem categoria' }} · {{ p.sku || 'Sem SKU' }}</small><span :class="['tag', !p.active ? 'muted-tag' : p.stock <= p.minimum_stock ? 'warning-tag' : 'ok-tag']">{{ !p.active ? 'Inativo' : p.stock <= p.minimum_stock ? 'Reposição' : 'Disponível' }}</span></div><div class="product-pricing"><strong>{{ money(p.sale_price) }}</strong><small>{{ p.stock }} unidades</small><div class="inline-actions"><button @click="editProduct(p)"><AppIcon name="edit" :size="14" /> Editar</button><button @click="toggleProduct(p)">{{ p.active ? 'Desativar' : 'Ativar' }}</button><button class="danger-text" @click="deleteProduct(p)"><AppIcon name="trash" :size="14" /></button></div></div></div></article></div>
    </section>

    <section v-if="tab === 'sales'">
      <header class="page-header"><div><span class="eyebrow">PDV / OPERAÇÕES</span><h1>Nova venda<span class="title-accent">.</span></h1><p>Selecione o produto no campo fixo e acompanhe o carrinho logo abaixo.</p></div><button class="btn secondary" @click="openModal('finance')"><AppIcon name="chart" :size="16" /> Relatórios</button></header>
      <div class="grid-2 sale-layout">
        <form class="panel sale-panel" @submit.prevent="registerSale">
          <div class="panel-heading"><div><span class="eyebrow">PONTO DE VENDA</span><h2>Adicionar item</h2></div><AppIcon name="cart" /></div>
          <div class="sale-draft"><div class="sale-product-field"><label for="sale-search">Pesquisar ou selecionar produto</label><div class="search-input"><AppIcon name="search" :size="16" /><input id="sale-search" ref="saleSearchInput" v-model="saleDraft.query" type="search" autocomplete="off" placeholder="Clique para ver produtos em ordem alfabética" @focus="showSaleOptions" @click="showSaleOptions" @input="onSaleInput" @blur="hideSaleOptions" aria-haspopup="listbox" :aria-expanded="saleSearchOpen" /></div>
            <div v-if="saleSearchOpen" class="sale-results" role="listbox" aria-label="Produtos disponíveis"><button v-for="p in saleChoices" :key="p.id" type="button" role="option" :aria-selected="saleDraft.product === p.id" @mousedown.prevent="chooseSaleItem(p)" @click="chooseSaleItem(p)"><span>{{ p.name }}<small>{{ p.sku || p.category_name || 'Sem categoria' }}</small></span><span>{{ money(p.sale_price) }}<small>{{ p.available_stock ?? p.stock }} disponíveis</small></span></button><div v-if="!saleChoices.length" class="empty">Nenhum produto disponível.</div></div>
            <small v-if="saleDraft.product" class="draft-selected"><AppIcon name="check" :size="14" /> Produto selecionado</small>
          </div><label class="qty-label">Quantidade<input v-model.number="saleDraft.quantity" type="number" min="1" step="1" :max="products.find(p => p.id === Number(saleDraft.product))?.available_stock ?? products.find(p => p.id === Number(saleDraft.product))?.stock" /></label><button type="button" class="btn primary" :disabled="!saleDraft.product || !Number.isInteger(Number(saleDraft.quantity)) || Number(saleDraft.quantity) < 1" @click="addItem"><AppIcon name="add" :size="17" /> Incluir</button></div>
          <div class="cart-heading"><h3>Itens adicionados</h3><span class="count-pill">{{ saleForm.items.length }} itens</span></div>
          <div v-if="!saleForm.items.length" class="empty cart-empty">Nenhum item na venda. Escolha um produto acima para começar.</div>
          <div v-for="(item, index) in saleForm.items" :key="item.key" class="cart-line"><span class="rank-index">{{ String(index + 1).padStart(2, '0') }}</span><div class="cart-line-name"><strong>{{ products.find(p => p.id === Number(item.product))?.name }}</strong><small>{{ money(products.find(p => p.id === Number(item.product))?.sale_price) }} / un.</small></div><label class="qty-label">Qtd.<input v-model.number="item.quantity" type="number" min="1" step="1" :max="products.find(p => p.id === Number(item.product))?.available_stock ?? products.find(p => p.id === Number(item.product))?.stock" /></label><strong class="cart-price">{{ money(Number(products.find(p => p.id === Number(item.product))?.sale_price || 0) * item.quantity) }}</strong><button type="button" class="remove-item" aria-label="Remover item" @click="removeItem(index)"><AppIcon name="trash" :size="17" /></button></div>
          <div class="sale-total"><div><span>Subtotal</span><strong>{{ money(subtotal) }}</strong></div><label>Desconto (R$)<input v-model.number="saleForm.discount" type="number" min="0" step="0.01" :max="subtotal" /></label><div class="grand-total"><span>Total da venda</span><strong>{{ money(total) }}</strong></div></div>
          <p v-if="saleForm.items.length && !cartValid" class="validation-hint">Confira quantidades, itens distintos e desconto.</p><button class="btn primary full" type="submit" :disabled="!cartValid || busy"><AppIcon name="check" :size="17" /> {{ busy ? 'Registrando…' : 'Finalizar venda' }}</button>
        </form>
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">REGISTROS</span><h2>Últimas vendas</h2></div><span class="count-pill">{{ sales.length }}</span></div><div v-if="!sales.length" class="empty">Ainda não existem vendas registradas.</div><div v-for="sale in sales.slice(0, 15)" :key="sale.id" class="detail-row"><div><strong>Venda #{{ sale.id }}</strong><small>{{ dateTime(sale.created_at) }} · {{ sale.items.length }} produto(s)</small></div><strong class="green-text">{{ money(sale.total) }}</strong></div></article>
      </div>
    </section>

    <section v-if="tab === 'inventory'"><header class="page-header"><div><span class="eyebrow">ESTOQUE / POSIÇÃO ATUAL</span><h1>Meu estoque<span class="title-accent">.</span></h1><p>Consulte o saldo, a situação de cada item e o valor investido em mercadorias.</p></div><button class="btn secondary" @click="exportXlsx('stock')"><AppIcon name="download" :size="17" /> Exportar Excel</button></header>
      <div class="inventory-kpis"><button class="inventory-kpi" @click="stockFilter = 'all'"><span><AppIcon name="layers" /></span><small>Produtos ativos</small><b>{{ stockOverview?.summary.products ?? inventoryCount.all }}</b></button><button class="inventory-kpi" @click="stockFilter = 'critico'"><span class="orange-text"><AppIcon name="alert" /></span><small>Estoque crítico</small><b>{{ inventoryCount.critico }}</b></button><button class="inventory-kpi" @click="stockFilter = 'a_vencer'"><span class="blue-text"><AppIcon name="calendar" /></span><small>Próximos do vencimento</small><b>{{ inventoryCount.a_vencer }}</b></button><button class="inventory-kpi" @click="stockFilter = 'vencido'"><span class="red-text"><AppIcon name="clock" /></span><small>Vencidos</small><b>{{ inventoryCount.vencido }}</b></button><div class="inventory-kpi inventory-total"><small>Valor estocado a custo</small><b>{{ money(stockOverview?.summary.inventory_value || 0) }}</b><small>{{ stockOverview?.summary.available_units ?? stockOverview?.summary.units ?? 0 }} disponíveis · {{ stockOverview?.summary.units ?? 0 }} físicas</small><small v-if="stockOverview?.summary.expired_stock_value">{{ money(stockOverview.summary.expired_stock_value) }} em mercadorias vencidas (a custo)</small></div></div>
      <article class="panel"><div class="panel-heading"><div><span class="eyebrow">INVENTÁRIO VISUAL</span><h2>Posição dos produtos</h2></div><span class="count-pill">{{ inventoryProducts.length }} resultados</span></div><div class="stock-filters"><label class="search-input"><AppIcon name="search" :size="17" /><input v-model="stockSearch" type="search" placeholder="Pesquisar nome, SKU ou categoria..." aria-label="Pesquisar estoque" /></label><select v-model="stockCategory" aria-label="Filtrar categoria"><option value="">Todas as categorias</option><option v-for="c in categories" :key="c.id" :value="String(c.id)">{{ c.name }}</option></select><select v-model="stockFilter" aria-label="Filtrar situação"><option value="all">Todas as situações</option><option value="normal">Em dia</option><option value="critico">Crítico</option><option value="a_vencer">A vencer</option><option value="vencido">Vencido</option><option value="inativo">Inativo</option></select></div><div v-if="!inventoryProducts.length" class="empty">Nenhum item corresponde aos filtros.</div><div v-else class="inventory-table-wrap"><table class="inventory-table"><thead><tr><th>Produto / SKU</th><th>Categoria</th><th>Saldo</th><th>Nível de estoque</th><th>Valor a custo</th><th>Situação</th><th></th></tr></thead><tbody><tr v-for="p in inventoryProducts" :key="p.id"><td><div class="item-cell"><span class="product-avatar"><AppIcon name="package" :size="17" /></span><div><strong>{{ p.name }}</strong><small>{{ p.sku || 'Sem SKU' }}</small></div></div></td><td>{{ p.category_name || 'Sem categoria' }}</td><td><strong>{{ p.stock }}</strong><small class="table-sub">Disponível: {{ p.available_stock ?? p.stock }}</small><small class="table-sub">Mín. {{ p.minimum_stock }}</small><small v-if="p.expired_units" class="table-sub negative">Vencido: {{ p.expired_units }}</small></td><td><div class="stock-progress"><div :class="{ 'progress-warning': Number(p.available_stock ?? p.stock) <= p.minimum_stock }" :style="{ width: `${Math.max(0, Math.min(100, (Number(p.available_stock ?? p.stock) / Math.max(1, p.minimum_stock * 2)) * 100))}%` }"></div></div></td><td>{{ money(Number(p.purchase_price) * p.stock) }}</td><td><span :class="['tag', inventoryStatus(p, today) === 'normal' ? 'ok-tag' : inventoryStatus(p, today) === 'critico' ? 'warning-tag' : inventoryStatus(p, today) === 'inativo' ? 'muted-tag' : 'danger-tag']">{{ labelStatus(p) }}</span></td><td><button class="small-action" @click="stockProduct = p.id; tab = 'movements'"><AppIcon name="arrows" :size="16" /> Ajustar</button></td></tr></tbody></table></div></article>
    </section>

    <section v-if="tab === 'movements'"><header class="page-header"><div><span class="eyebrow">ESTOQUE / RASTREABILIDADE</span><h1>Movimentações<span class="title-accent">.</span></h1><p>Registre entradas e saídas com justificativa. Consulte o histórico detalhado.</p></div><button class="btn secondary" @click="openInventory()"><AppIcon name="package" :size="16" /> Ver estoque</button></header><div class="grid-form"><form class="panel" @submit.prevent="adjustStock"><div class="panel-heading"><div><span class="eyebrow">ENTRADA / SAÍDA</span><h2>Ajustar saldo</h2></div><AppIcon name="arrows" /></div><label>Produto<select v-model="stockProduct" required><option value="">Selecione um produto</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} · {{ p.stock }} un.</option></select></label><label>Quantidade (positiva = entrada; negativa = saída)<input v-model.number="stockDelta" type="number" step="1" required /></label><label>Justificativa<select v-model="stockReason" required><option v-for="r in MOVEMENT_REASONS" :key="r.value" :value="r.value" :disabled="r.direction !== 'both' && r.direction !== (Number(stockDelta) > 0 ? 'in' : 'out')">{{ r.label }}</option></select></label><label v-if="stockReason === 'outro' || stockReason === 'inventario' || stockCustomNote">{{ stockReason === 'outro' ? 'Descreva o motivo (obrigatório)' : 'Detalhes adicionais (opcional)' }}<input v-model="stockCustomNote" maxlength="180" :required="stockReason === 'outro'" placeholder="Explique o ocorrido..." /></label><label v-if="showingReceiptExpiry">Nova validade do lote<input v-model="stockExpiry" type="date" required :min="localDateISO()" /><small>Essa validade será registrada apenas para as unidades recebidas, sem substituir os lotes anteriores.</small></label><p v-if="selectedMovementProduct?.perishable && Number(stockDelta) < 0" class="help-text">A baixa desconta primeiro o lote mais próximo do vencimento, incluindo lotes vencidos para descarte.</p><p v-if="!movementDirectionValid" class="validation-hint">A justificativa selecionada não corresponde ao sentido da movimentação.</p><button class="btn primary" type="submit" :disabled="busy || !movementFormValid"><AppIcon name="check" :size="17" /> {{ busy ? 'Salvando…' : 'Registrar movimentação' }}</button></form><article class="panel"><div class="panel-heading"><div><span class="eyebrow">AUDITORIA</span><h2>Histórico de estoque</h2></div><span class="count-pill">{{ filteredMovements.length }} registros</span></div><label>Filtrar por produto<select v-model="movementProduct"><option value="">Todos os produtos</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option></select></label><div v-if="!filteredMovements.length" class="empty">Nenhum movimento encontrado.</div><div v-for="m in filteredMovements.slice(0, 50)" :key="m.id" class="detail-row"><div><strong>{{ m.product_name }}</strong><small>{{ m.justification_display || m.reason_display }} · {{ m.note || 'Sem observação' }}</small><small>{{ m.stock_before }} → {{ m.stock_after }} un. · {{ dateTime(m.created_at) }}</small><small v-for="(lot, li) in m.lots" :key="li">Lote: {{ lot.quantity > 0 ? "+" : "" }}{{ lot.quantity }} un. · Validade {{ shortDate(lot.expiration_date) }}</small></div><span :class="['change-amount', m.delta > 0 ? 'positive' : 'negative']">{{ m.delta > 0 ? '+' : '' }}{{ m.delta }}</span></div></article></div></section>
    <footer class="app-footer" aria-label="Rodapé do Comercializa">
      <div class="footer-brand">
        <img :src="BRAND_ASSETS.horizontalOnLight" alt="Comercializa" class="footer-logo footer-logo-light" width="174" height="32" />
        <img :src="BRAND_ASSETS.horizontalOnDark" alt="Comercializa" class="footer-logo footer-logo-dark" width="174" height="32" />
      </div>
      <div class="footer-copy">
        <span>Desenvolvido por <strong>Arthur Azevêdo</strong></span>
        <small>© {{ copyrightYear }} Comercializa. Todos os direitos reservados.</small>
      </div>
    </footer>
  </main>

  <div v-if="modal" class="modal-backdrop" @click.self="closeModal"><section class="modal" role="dialog" aria-modal="true" :aria-label="modalTitles[modal]"><header class="modal-header"><div><span class="eyebrow">{{ modal === 'finance' ? 'RELATÓRIOS' : 'ALERTAS DE ESTOQUE' }}</span><h2>{{ modalTitles[modal] }}</h2></div><button class="icon-btn" aria-label="Fechar janela" @click="closeModal"><AppIcon name="close" /></button></header>
    <template v-if="modal === 'finance'"><div class="modal-body"><p class="help-text" style="margin-bottom:18px">Receita após descontos (não equivale a lucro líquido). Filtre o intervalo e explore produtos e categorias.</p><form class="report-filters" @submit.prevent="refreshFinance"><label>Início<input v-model="reportFilters.start" type="date" required /></label><label>Fim<input v-model="reportFilters.end" type="date" required /></label><label>Categoria<select v-model="reportFilters.category"><option value="">Todas</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></label><label>Produto<select v-model="reportFilters.product"><option value="">Todos</option><option v-for="p in products.filter(p => !reportFilters.category || String(p.category) === String(reportFilters.category))" :key="p.id" :value="p.id">{{ p.name }}</option></select></label><button class="btn primary" type="submit" :disabled="financeLoading"><AppIcon name="filter" :size="16" /> {{ financeLoading ? 'Consultando…' : 'Aplicar' }}</button></form><div class="report-actions"><button type="button" class="btn secondary" @click="reportFilters = defaultReportFilters(); refreshFinance()">Mês atual</button><button type="button" class="btn secondary" @click="reportFilters = { ...reportFilters, start: `${new Date().getFullYear()}-01-01`, end: localDateISO() }; refreshFinance()">Ano atual</button><button class="btn secondary" @click="exportXlsx('finance')"><AppIcon name="download" :size="16" /> Exportar Excel</button></div><div v-if="finance" class="report-content"><div class="report-summary"><div><small>Receita após descontos</small><strong>{{ money(finance.summary.revenue) }}</strong></div><div><small>Vendas</small><strong>{{ finance.summary.sales_count }}</strong></div><div><small>Unidades vendidas</small><strong>{{ finance.summary.items_sold }}</strong></div><div><small>Ticket médio</small><strong>{{ money(finance.summary.average_ticket) }}</strong></div></div><div class="report-explanation">Bruto: {{ money(finance.summary.gross) }} · Descontos atribuídos: {{ money(finance.summary.discounts) }}. A análise considera somente os filtros aplicados.</div><div class="report-grid"><div><h3>Desempenho por categoria</h3><div v-if="!finance.categories.length" class="empty">Sem vendas neste período.</div><div v-for="c in finance.categories" :key="c.name" class="detail-row"><div><strong>{{ c.name }}</strong><small>{{ c.quantity }} unidades</small></div><b>{{ money(c.revenue) }}</b></div></div><div><h3>Produtos vendidos</h3><div v-if="!finance.products.length" class="empty">Sem itens vendidos.</div><div v-for="p in finance.products" :key="p.id" class="detail-row"><div><strong>{{ p.name }}</strong><small>{{ p.category }} · {{ p.quantity }} un.</small></div><b>{{ money(p.revenue) }}</b></div></div></div><h3 style="margin-top:24px">Evolução por dia</h3><div v-if="!finance.daily.length" class="empty">Nenhuma venda no período selecionado.</div><div v-for="d in finance.daily" :key="d.date" class="detail-row"><span>{{ shortDate(d.date) }}</span><span>{{ d.quantity }} unidades</span><strong>{{ money(d.revenue) }}</strong></div></div></div></template>
    <template v-else><div class="modal-body"><p class="help-text">{{ modal === 'critico' ? 'Produtos ativos com saldo igual ou inferior ao estoque mínimo, inclusive itens com validade comprometida.' : modal === 'vencido' ? 'Produtos ativos com saldo disponível e validade já ultrapassada.' : 'Produtos ativos que vencem nos próximos 15 dias, incluindo hoje.' }}</p><div v-if="!modalItems.length" class="empty">Nenhum produto nesta situação.</div><div v-for="p in modalItems" :key="p.id" class="modal-product"><span class="product-avatar"><AppIcon name="package" /></span><div><strong>{{ p.name }}</strong><small>{{ p.category_name || 'Sem categoria' }} · {{ p.sku || 'Sem SKU' }}</small><small v-if="p.nearest_expiration || p.expiration_date">Validade mais próxima: {{ shortDate(p.nearest_expiration || p.expiration_date) }}</small></div><div class="modal-product-end"><b>{{ p.stock }} un.</b><small>Vendável: {{ p.available_stock ?? p.stock }}</small><small>Mínimo: {{ p.minimum_stock }}</small></div></div></div><footer class="modal-footer"><button class="btn secondary" @click="closeModal">Fechar</button><button class="btn primary" @click="openInventory(modal)">Ver na tela de estoque <AppIcon name="arrow" :size="15" /></button></footer></template>
  </section></div>
</div>
</template>
