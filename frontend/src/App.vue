<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { api, postWithRecovery, isTransientFailure, getAuthToken, saveAuthToken, clearAuthToken } from './api'
import { actionableWriteMessage } from './operationFeedback'
import { createLatestLoader, upsertById, removeById } from './dataSync'
import AppIcon from './components/AppIcon.vue'
import NumericField from './components/NumericField.vue'
import ProductThumbnail from './components/ProductThumbnail.vue'
import { normalizeProductPhoto } from './imageProcessing'
import { addOrIncrementCartItem } from './cart'
import { APP_VERSION } from './version'
import DecisionChart from './components/DecisionChart.vue'
import { sortedSaleOptions, MOVEMENT_REASONS, movementNote, periodDates, aggregateDaily, productChartData, rankingDonutRows, concentrationPercentage } from './charts'
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
const financeError = ref(false)
const syncDelayed = ref(false)
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
const productPhoto = ref(null)
const photoPreviewUrl = ref('')
const photoBusy = ref(false)
const photoError = ref('')
const removePhoto = ref(false)
const photoGalleryInput = ref(null)
const photoCameraInput = ref(null)
let photoPickSequence = 0
function clearPhotoState() {
  ++photoPickSequence
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoPreviewUrl.value = ''
  productPhoto.value = null
  removePhoto.value = false
  photoError.value = ''
  photoBusy.value = false
}
async function selectPhoto(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return
  const sequence = ++photoPickSequence
  photoBusy.value = true
  photoError.value = ''
  try {
    const processed = await normalizeProductPhoto(file, productForm.value.sku || productForm.value.id)
    if (sequence !== photoPickSequence) return
    if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
    photoPreviewUrl.value = URL.createObjectURL(processed)
    productPhoto.value = processed
    removePhoto.value = false
  } catch (error) {
    if (sequence === photoPickSequence) photoError.value = error.message || 'Falha ao preparar fotografia.'
  } finally { if (sequence === photoPickSequence) photoBusy.value = false }
}
function discardPhoto() {
  ++photoPickSequence
  if (photoPreviewUrl.value) URL.revokeObjectURL(photoPreviewUrl.value)
  photoPreviewUrl.value = ''
  productPhoto.value = null
  removePhoto.value = Boolean(productForm.value.id && productForm.value.has_image)
  photoBusy.value = false
  photoError.value = ''
}
const saleForm = ref({ items: [], discount: 0 })
const saleToReverse = ref(null)
const reversalReason = ref('Devolução integral')
const reversalDetails = ref('')
const reversalReasons = ['Devolução integral', 'Erro de lançamento', 'Cancelamento da compra', 'Outro motivo']
const reversalValid = computed(() => !!saleToReverse.value &&
  (reversalReason.value !== 'Outro motivo' || reversalDetails.value.trim().length >= 3))
const saleDraft = ref({ product: '', quantity: 1, query: '' })
const saleSearchOpen = ref(false)
const saleSearchInput = ref(null)
let saleSearchBlurTimer = null
let cartItemSequence = 0
const chartPeriod = ref('30d')
const chartGrouping = ref('day')
const chartMetric = ref('revenue')
const dashboardReport = ref(null)
const chartLoading = ref(false)
const chartError = ref(false)
const chartUpdatedAt = ref('')
const serverWaking = ref(false)
let serverWakingTimer
let dashboardChartRequest = 0
let chartAbortController = null
let chartErrorTimer = null
const chartCache = new Map()
let activeRefreshInterval
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
const rankedRows = computed(() => rankingDonutRows(dashboardReport.value?.products || [], 'quantity', 10))
const rankedProducts = computed(() => [...(dashboardReport.value?.products || [])].filter(p => Number(p.quantity) > 0).sort((a, b) => Number(b.quantity || 0) - Number(a.quantity || 0) || String(a.name).localeCompare(String(b.name), 'pt-BR')).slice(0, 10))
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
const modalTitles = { critico: 'Produtos em estoque crítico', vencido: 'Produtos vencidos', a_vencer: 'Próximos do vencimento', finance: 'Análise financeira e vendas', 'sale-reversal': 'Estornar venda' }

watch(theme, value => { document.documentElement.dataset.theme = value; saveTheme(value) }, { immediate: true })
watch(modal, value => { document.body.style.overflow = value ? 'hidden' : '' })
watch(() => reportFilters.value.category, () => { reportFilters.value.product = '' })
watch(chartPeriod, period => {
  if (period === '90d') chartGrouping.value = 'week'
  else if (period === '12m') chartGrouping.value = 'month'
  else chartGrouping.value = 'day'
  void refreshDashboardCharts()
})
watch(tab, selected => {
  if (!authenticated.value) return
  const onDemand = { dashboard: ['dashboard'], sales: ['sales'], products: ['products', 'categories'], inventory: ['stockOverview', 'products'], movements: ['movements', 'products'] }
  void refreshResources(onDemand[selected] || [])
  if (selected === 'dashboard') void refreshDashboardCharts({ silent: true, force: true })
})
watch(stockProduct, () => { stockExpiry.value = '' })
watch(stockDelta, value => { if (Number(value) <= 0) { stockExpiry.value = ''; if (stockReason.value === 'recebimento' || stockReason.value === 'devolucao') stockReason.value = 'avaria' } else if (stockReason.value === 'avaria' || stockReason.value === 'perda') stockReason.value = 'recebimento' })
function onKeydown(event) { if (event.key === 'Escape') closeModal() }
onMounted(() => {
  window.addEventListener('keydown', onKeydown)
  yearRefreshInterval = window.setInterval(() => { copyrightYear.value = getCopyrightYear() }, 60_000)
  activeRefreshInterval = window.setInterval(() => {
    if (!authenticated.value || document.visibilityState !== 'visible') return
    if (tab.value === 'dashboard') {
      void refreshResources(['dashboard'], { force: true })
      if (!chartLoading.value) void refreshDashboardCharts({ silent: true, force: true })
    } else if (tab.value === 'sales') {
      void refreshResources(['sales', 'products'], { force: true })
    }
  }, 20000)
  window.addEventListener('online', onAppResume)
  document.addEventListener('visibilitychange', onAppResume)
  window.addEventListener('comercializa:unauthorized', onUnauthorized)
  initializeSession()
})
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('comercializa:unauthorized', onUnauthorized)
  window.clearInterval(yearRefreshInterval)
  window.clearInterval(activeRefreshInterval)
  window.clearTimeout(serverWakingTimer)
  chartAbortController?.abort()
  window.clearTimeout(chartErrorTimer)
  window.removeEventListener('online', onAppResume)
  document.removeEventListener('visibilitychange', onAppResume)
  toastController.dispose()
  clearPhotoState()
  window.clearTimeout(saleSearchBlurTimer)
  document.body.style.overflow = ''
})
function onUnauthorized() {
  if (!authRequired.value) return
  // Uma requisição iniciada antes do logout não pode restaurar dados da sessão.
  for (const name of Object.keys(resourceEndpoints)) resourceLoader.invalidate(name)
  ++dashboardChartRequest
  chartAbortController?.abort()
  chartCache.clear()
  loadedAt.clear()
  dashboardReport.value = null
  stockOverview.value = null
  finance.value = null
  authenticated.value = false
  authUsername.value = ''
  dashboard.value = null
  products.value = []
  categories.value = []
  sales.value = []
  movements.value = []
  loginError.value = 'Sua sessão expirou ou foi encerrada. Entre novamente.'
}
function onAppResume() {
  if (!authenticated.value || document.visibilityState !== 'visible') return
  void refreshResources(tab.value === 'dashboard' ? ['dashboard'] : [({
    inventory: 'stockOverview', sales: 'sales', movements: 'movements', products: 'products',
  })[tab.value] || 'dashboard'], { force: true })
  if (tab.value === 'dashboard') void refreshDashboardCharts({ silent: true, force: true })
}
async function initializeSession() {
  authChecking.value = true
  serverWaking.value = false
  window.clearTimeout(serverWakingTimer)
  serverWakingTimer = window.setTimeout(() => { serverWaking.value = true }, 5500)
  authStartupError.value = ''
  try {
    const { data } = await api.get('auth/status/')
    authRequired.value = Boolean(data.authentication_required)
    authenticated.value = !authRequired.value || Boolean(data.authenticated)
    authUsername.value = data.username || ''
    if (authenticated.value) {
      void loadAll()
      void refreshDashboardCharts({ silent: true })
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
  } finally { authChecking.value = false; serverWaking.value = false; window.clearTimeout(serverWakingTimer) }
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
    void loadAll()
    void refreshDashboardCharts({ silent: true })
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
function closeToastAtProgressEnd(id) { if (toast.value?.id === id) toastController.dismiss() }
function notifyWriteFailure(error) {
  // Sem HTTP 2xx não afirmamos sucesso nem fracasso: a gravação pode ter
  // ocorrido no servidor. Nunca mostrar o erro genérico de conexão no PDV.
  // Apenas um erro de validação/permissão com resposta explícita do servidor
  // vira notificação; as demais falhas permanecem no console para diagnóstico.
  const message = actionableWriteMessage(error)
  if (message) {
    alertUser(message, 'error')
    return
  }
  if (error?.response?.status !== 401) {
    console.warn('Resposta inconclusiva da gravação; consultando os dados:', error)
    syncDelayed.value = true
    refreshVisibleData()
  }
}
function notifyReadFailure(error) {
  // Relatórios já indicam problema no próprio painel. Não transformar falhas
  // de consulta em pop-up de "conexão com API" na tela do operador.
  console.warn('Consulta não atualizada:', error)
  if (error?.response?.status !== 401 && error?.code !== 'ERR_CANCELED') syncDelayed.value = true
}
function applyConfirmedWrite(updateUI, response) {
  // O sucesso HTTP é definitivo. Uma falha reativa/local NÃO pode ser
  // apresentada como falha da gravação no servidor.
  try { updateUI(response) }
  catch (error) {
    console.error('Operação confirmada, mas a interface não sincronizou:', error)
    refreshVisibleData()
  }
}

function errorText(error) {
  const data = error?.response?.data
  if (!data) return 'Não foi possível concluir a solicitação. Tente novamente.'
  if (typeof data === 'string') return data
  if (data.detail) return String(data.detail)
  return Object.entries(data).map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(', ') : typeof value === 'object' ? JSON.stringify(value) : value}`).join(' · ')
}
// Cada lista é consultada separadamente. Respostas antigas não podem sobrescrever
// alterações que já foram confirmadas e mostradas na interface.
const resourceEndpoints = {
  products: ['products/', products],
  categories: ['categories/', categories],
  dashboard: ['dashboard/', dashboard],
  sales: ['sales/', sales],
  movements: ['stock-movements/', movements],
  stockOverview: ['stock-overview/', stockOverview],
}
const loadedAt = new Map()
const resourceLoader = createLatestLoader(
  async name => (await api.get(resourceEndpoints[name][0])).data,
  (name, data) => {
    resourceEndpoints[name][1].value = data
    loadedAt.set(name, Date.now())
  },
)
async function refreshResources(names, { force = false } = {}) {
  const required = [...new Set(names)].filter(name => resourceEndpoints[name] &&
    (force || !loadedAt.has(name) || Date.now() - loadedAt.get(name) > 25000))
  if (!required.length) return true
  const results = await Promise.allSettled(required.map(name => resourceLoader.load(name)))
  const failed = results.filter(result => result.status === 'rejected')
  if (failed.length) {
    console.warn('Consultas não atualizadas:', failed.map(result => result.reason))
    if (failed.some(result => isTransientFailure(result.reason) || Number(result.reason?.response?.status) >= 500)) syncDelayed.value = true
  } else {
    syncDelayed.value = false
  }
  // Falhas de atualização de listas não se transformam em toasts: consultas
  // automáticas são frequentes e dados anteriormente carregados seguem válidos.
  return !failed.length
}
async function loadAll() {
  loading.value = true
  // Carrega só o necessário para a primeira tela; histórico e estoque sob demanda.
  try { await refreshResources(['products', 'categories', 'dashboard']) }
  finally { loading.value = false }
}
function invalidateResource(...names) {
  for (const name of names) {
    resourceLoader.invalidate(name)
    loadedAt.delete(name)
  }
}
function refreshCatalogInBackground() {
  invalidateResource('products', 'dashboard', 'stockOverview')
  const names = tab.value === 'inventory' ? ['products', 'dashboard', 'stockOverview'] : ['products', 'dashboard']
  void refreshResources(names, { force: true })
}
function refreshVisibleData() {
  const names = { dashboard: ['products', 'dashboard'], products: ['products', 'categories'], sales: ['sales', 'products'], inventory: ['products', 'stockOverview'], movements: ['movements', 'products'] }
  void refreshResources(names[tab.value] || ['dashboard'], { force: true })
  if (tab.value === 'dashboard') void refreshDashboardCharts({ force: true })
}
function resetProduct() { clearPhotoState(); productForm.value = blankProduct() }
function editProduct(product) {
  clearPhotoState()
  productForm.value = { ...product, category: product.category ?? '', expiration_date: product.expiration_date ?? '' }
  tab.value = 'products'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
async function saveProduct() {
  if (busy.value || photoBusy.value) return
  busy.value = true
  photoError.value = ''
  const payload = { ...productForm.value, category: productForm.value.category || null,
    sku: productForm.value.sku || null, expiration_date: productForm.value.expiration_date || null }
  const wasEditing = Boolean(payload.id)
  let saved = null
  try {
    const response = wasEditing
      ? await api.put(`products/${payload.id}/`, payload)
      : await postWithRecovery('products/', payload)
    saved = response.data
  } catch (error) {
    notifyWriteFailure(error)
    busy.value = false
    return
  }
  // Uma eventual falha na foto NÃO significa falha no cadastro do produto.
  // Em novos cadastros, conservamos o id para tentar a foto via edição, sem duplicar.
  productForm.value.id = saved.id
  try {
    if (productPhoto.value) {
      const form = new FormData()
      form.append('image', productPhoto.value, productPhoto.value.name)
      const upload = await api.put(`products/${saved.id}/image/`, form)
      saved = { ...saved, ...upload.data }
    } else if (removePhoto.value && wasEditing) {
      const removed = await api.delete(`products/${saved.id}/image/`)
      saved = { ...saved, ...removed.data }
    }
  } catch (error) {
    photoError.value = `Produto salvo, mas a foto não foi atualizada. ${errorText(error)}`
    products.value = upsertById(products.value, saved)
    invalidateResource('products')
    refreshCatalogInBackground()
    alertUser('Produto salvo. Confira a foto antes de continuar.', 'error')
    busy.value = false
    return
  }
  products.value = upsertById(products.value, saved)
  invalidateResource('products')
  resetProduct()
  alertUser(wasEditing ? 'Produto atualizado com sucesso.' : 'Produto cadastrado com sucesso.')
  refreshCatalogInBackground()
  busy.value = false
}

async function toggleProduct(product) {
  if (busy.value) return
  busy.value = true
  try {
    const response = await api.patch(`products/${product.id}/`, { active: !product.active })
    applyConfirmedWrite(() => {
      invalidateResource('products')
      products.value = upsertById(products.value, response.data)
      alertUser('Situação do produto atualizada.')
      refreshCatalogInBackground()
    }, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}
async function deleteProduct(product) {
  if (busy.value || !confirm(`Excluir "${product.name}"? Produtos com histórico devem ser desativados.`)) return
  busy.value = true
  try {
    const response = await api.delete(`products/${product.id}/`)
    applyConfirmedWrite(() => {
      invalidateResource('products')
      products.value = removeById(products.value, product.id)
      if (productForm.value.id === product.id) resetProduct()
      alertUser('Produto excluído.')
      refreshCatalogInBackground()
    }, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}
async function addCategory() {
  if (busy.value || !categoryName.value.trim()) return
  busy.value = true
  const submittedName = categoryName.value.trim()
  const onSaved = response => {
    invalidateResource('categories')
    categories.value = upsertById(categories.value, response.data)
    if (categoryName.value.trim() === submittedName) categoryName.value = ''
    alertUser('Categoria criada com sucesso.')
    void refreshResources(['categories'], { force: true })
  }
  try {
    const response = await postWithRecovery('categories/', { name: submittedName })
    applyConfirmedWrite(onSaved, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}
function addItem() {
  if (!saleDraft.value.product) return
  const product = products.value.find(p => p.id === Number(saleDraft.value.product))
  const result = addOrIncrementCartItem(saleForm.value.items, product, saleDraft.value.quantity, cartItemSequence + 1)
  if (!result.ok) { alertUser(result.reason, 'error'); return }
  if (!result.merged) ++cartItemSequence
  saleForm.value.items = result.items
  saleDraft.value = { product: '', quantity: 1, query: '' }
  saleSearchOpen.value = false
  nextTick(() => saleSearchInput.value?.focus())
}
function removeItem(i) { saleForm.value.items.splice(i, 1) }
function chooseSaleItem(p) { window.clearTimeout(saleSearchBlurTimer); saleDraft.value.product = p.id; saleDraft.value.query = p.name; saleSearchOpen.value = false }
function showSaleOptions() { window.clearTimeout(saleSearchBlurTimer); saleSearchOpen.value = true }
function onSaleInput() { saleDraft.value.product = ''; saleSearchOpen.value = true }
function clearSaleSearch() {
  saleDraft.value.product = ''
  saleDraft.value.query = ''
  showSaleOptions()
  nextTick(() => saleSearchInput.value?.focus())
}
function toggleSaleOptions() {
  saleSearchOpen.value = !saleSearchOpen.value
  if (saleSearchOpen.value) nextTick(() => saleSearchInput.value?.focus())
}
function hideSaleOptions() { window.clearTimeout(saleSearchBlurTimer); saleSearchBlurTimer = window.setTimeout(() => { saleSearchOpen.value = false }, 250) }
async function refreshDashboardCharts({ silent = false, force = false } = {}) {
  const cacheKey = `${chartPeriod.value}|${localDateISO()}`
  const cached = chartCache.get(cacheKey)
  if (!force && cached && Date.now() - cached.at < 7000) {
    ++dashboardChartRequest
    chartAbortController?.abort()
    chartLoading.value = false
    chartError.value = false
    dashboardReport.value = cached.data
    chartUpdatedAt.value = cached.time
    return
  }
  if (chartLoading.value && !force) return
  const requestId = ++dashboardChartRequest
  chartAbortController?.abort()
  chartAbortController = new AbortController()
  chartLoading.value = true
  chartError.value = false
  window.clearTimeout(chartErrorTimer)
  try {
    const dates = periodDates(chartPeriod.value, localDateISO())
    const result = await api.get(`reports/finance/?${queryReport(dates)}`, { signal: chartAbortController.signal })
    if (requestId === dashboardChartRequest) {
      dashboardReport.value = result.data
      syncDelayed.value = false
      const now = Date.now()
      chartUpdatedAt.value = new Date(now).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
      chartCache.set(cacheKey, { data: result.data, at: now, time: chartUpdatedAt.value })
    }
  } catch (error) {
    if (requestId === dashboardChartRequest && error?.code !== 'ERR_CANCELED') {
      chartError.value = true
      chartErrorTimer = window.setTimeout(() => { chartError.value = false }, 5500)
      // Falha temporária da consulta não é falha de operação, mesmo no clique
      // manual em atualizar; mantém o relatório anterior sem toast de API.
      console.warn('Gráfico não atualizado:', error)
      if (isTransientFailure(error)) syncDelayed.value = true
      // Erros são indicados no próprio painel apenas quando não há dados anteriores.
    }
  } finally { if (requestId === dashboardChartRequest) chartLoading.value = false }
}
function refreshChartsAfterWrite() {
  chartCache.clear()
  finance.value = null
  // Mantém as estatísticas coerentes em qualquer aba, não apenas no dashboard.
  // A tela de vendas mostra a venda confirmada imediatamente; o GET reconcilia.
  invalidateResource('products', 'dashboard', 'movements', 'stockOverview', 'sales')
  const visible = {
    dashboard: ['products', 'dashboard'],
    sales: ['products', 'dashboard', 'sales'],
    inventory: ['products', 'dashboard', 'stockOverview'],
    movements: ['products', 'dashboard', 'movements'],
    products: ['products', 'dashboard'],
  }
  void refreshResources(visible[tab.value] || ['products', 'dashboard'], { force: true })
  void refreshDashboardCharts({ silent: true, force: true })
  if (modal.value === 'finance') void refreshFinance()
}

function openReversal(sale) {
  if (busy.value || sale.canceled_at) return
  saleToReverse.value = sale
  reversalReason.value = 'Devolução integral'
  reversalDetails.value = ''
  modal.value = 'sale-reversal'
}
async function confirmReversal() {
  if (busy.value || !reversalValid.value) return
  busy.value = true
  const saleId = saleToReverse.value.id
  const reason = reversalReason.value === 'Outro motivo'
    ? reversalDetails.value.trim() : reversalReason.value
  const onSaved = response => {
    const data = response.data
    sales.value = upsertById(sales.value, data)
    if (saleToReverse.value?.id === saleId) closeModal()
    alertUser(`Venda #${data.id} estornada. Estoque devolvido e reembolso de ${money(data.refunded_amount)} registrado.`)
    refreshChartsAfterWrite()
  }
  try {
    const response = await postWithRecovery(`sales/${saleId}/cancel/`, { reason })
    applyConfirmedWrite(onSaved, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}

async function registerSale() {
  if (!cartValid.value || busy.value) return
  busy.value = true
  const submittedForm = JSON.stringify(saleForm.value)
  const payload = { discount: Number(saleForm.value.discount) || 0, items: saleForm.value.items.map(i => ({ product: Number(i.product), quantity: Number(i.quantity) })) }
  const onSaved = response => {
    invalidateResource('sales')
    sales.value = upsertById(sales.value, response.data)
    if (JSON.stringify(saleForm.value) === submittedForm) {
      saleForm.value = { items: [], discount: 0 }
      saleDraft.value = { product: '', quantity: 1, query: '' }
    }
    alertUser('Venda registrada! Estoque atualizado no servidor.')
    refreshChartsAfterWrite()
  }
  try {
    const response = await postWithRecovery('sales/', payload)
    applyConfirmedWrite(onSaved, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}
async function adjustStock() {
  if (busy.value || !movementFormValid.value) return
  busy.value = true
  const originalForm = JSON.stringify([stockProduct.value, stockDelta.value, stockReason.value, stockCustomNote.value, stockExpiry.value])
  const payload = { product: Number(stockProduct.value), delta: Number(stockDelta.value), note: stockNote.value, justification: stockReason.value, ...(showingReceiptExpiry.value ? { expiration_date: stockExpiry.value } : {}) }
  const onSaved = response => {
    invalidateResource('movements')
    movements.value = upsertById(movements.value, response.data)
    if (JSON.stringify([stockProduct.value, stockDelta.value, stockReason.value, stockCustomNote.value, stockExpiry.value]) === originalForm) {
      stockDelta.value = 1; stockReason.value = 'recebimento'; stockCustomNote.value = ''; stockExpiry.value = ''
    }
    alertUser('Movimentação registrada com sucesso.')
    refreshChartsAfterWrite()
  }
  try {
    const response = await postWithRecovery('stock-movements/', payload)
    applyConfirmedWrite(onSaved, response)
  } catch (error) { notifyWriteFailure(error) }
  finally { busy.value = false }
}
function openModal(type) { modal.value = type; if (type === 'finance') refreshFinance() }
function closeModal() { modal.value = ''; saleToReverse.value = null }
function openInventory(status = 'all') { tab.value = 'inventory'; stockFilter.value = status; closeModal() }
async function refreshFinance() {
  if (!reportFilters.value.start || !reportFilters.value.end || reportFilters.value.start > reportFilters.value.end) { alertUser('Corrija o intervalo de datas.', 'error'); return }
  financeLoading.value = true
  financeError.value = false
  try {
    finance.value = (await api.get(`reports/finance/?${queryReport(reportFilters.value)}`)).data
    syncDelayed.value = false
  } catch (error) {
    financeError.value = true
    notifyReadFailure(error)
  } finally { financeLoading.value = false }
}
async function exportXlsx(type) {
  try {
    const url = type === 'stock' ? 'stock-export/' : `reports/finance/export/?${queryReport(reportFilters.value)}`
    const response = await api.get(url, { responseType: 'blob', timeout: 60000 })
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const link = document.createElement('a'); const urlObject = URL.createObjectURL(blob)
    link.href = urlObject; link.download = type === 'stock' ? 'comercializa_estoque.xlsx' : 'comercializa_financeiro.xlsx'
    document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(urlObject), 1200)
  } catch (error) {
    console.warn('Exportação indisponível:', error)
    alertUser('Não foi possível gerar o arquivo agora. Tente novamente.', 'error')
  }
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
    <img :src="theme === 'dark' ? BRAND_ASSETS.horizontalOnDark : BRAND_ASSETS.horizontalOnLight" alt="Comercializa" class="auth-logo" width="360" height="66" />
    <template v-if="authChecking">
      <h1>Conectando ao Comercializa…</h1>
      <p>Verificando o acesso ao sistema.</p>
      <p v-if="serverWaking" class="auth-waking" role="status"><AppIcon name="refresh" :size="16" /> O servidor gratuito está iniciando. Seus dados permanecem seguros.</p>
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
    </div>
    <div class="sidebar-label">MENU PRINCIPAL</div>
    <nav aria-label="Navegação principal">
      <button :class="{ active: tab === 'dashboard' }" :aria-current="tab === 'dashboard' ? 'page' : undefined" @click="tab = 'dashboard'"><AppIcon name="dashboard" /> Visão geral</button>
      <button :class="{ active: tab === 'sales' }" :aria-current="tab === 'sales' ? 'page' : undefined" @click="tab = 'sales'"><AppIcon name="cart" /> Vendas</button>
      <button :class="{ active: tab === 'products' }" :aria-current="tab === 'products' ? 'page' : undefined" @click="tab = 'products'"><AppIcon name="products" /> Produtos</button>
      <button :class="{ active: tab === 'inventory' }" :aria-current="tab === 'inventory' ? 'page' : undefined" @click="tab = 'inventory'"><AppIcon name="package" /> Ver estoque</button>
      <button :class="{ active: tab === 'movements' }" :aria-current="tab === 'movements' ? 'page' : undefined" @click="tab = 'movements'"><AppIcon name="arrows" /> Movimentações</button>
    </nav>
    <div class="sidebar-footer"><div class="sidebar-footer-head"><span class="status-dot"></span> {{ syncDelayed ? 'Mostrando últimos dados' : authRequired ? 'Ambiente conectado' : 'Ambiente de desenvolvimento' }}</div><small>Gestão de loja de variedades · Versão {{ APP_VERSION }}</small></div>
  </aside>
  <main class="main-content">
    <div class="topbar"><span class="topbar-path">PAINEL <span class="crumb">/ {{ { dashboard: 'Visão geral', sales: 'Vendas', products: 'Produtos', inventory: 'Posição de estoque', movements: 'Movimentações' }[tab] }}</span></span><div class="topbar-actions"><span class="topbar-date">{{ shortDate(today) }}</span><button type="button" class="icon-btn" :title="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'" :aria-label="theme === 'dark' ? 'Ativar tema claro' : 'Ativar tema escuro'" @click="theme = theme === 'dark' ? 'light' : 'dark'"><AppIcon :name="theme === 'dark' ? 'sun' : 'moon'" /></button><button type="button" class="icon-btn" aria-label="Atualizar dados" title="Atualizar dados" @click="refreshVisibleData"><AppIcon name="refresh" /></button><span v-if="authRequired" class="topbar-user">{{ authUsername }}</span><button v-if="authRequired" type="button" class="btn secondary" title="Sair da conta" @click="signOut">Sair</button></div></div>
    <Transition name="toast"><div v-if="toast" :key="toast.id" :class="['toast-notice', toast.type]" :role="toast.type === 'error' ? 'alert' : 'status'" :aria-live="toast.type === 'error' ? 'assertive' : 'polite'"><span class="toast-glyph"><AppIcon :name="toast.type === 'error' ? 'alert' : 'check'" :size="20" /></span><span>{{ toast.text }}</span><button type="button" aria-label="Dispensar notificação" @click="toastController.dismiss()"><AppIcon name="close" :size="17" /></button><span class="toast-timer" aria-hidden="true" @animationend="closeToastAtProgressEnd(toast.id)"></span></div></Transition>
    <div v-if="loading && !dashboard" class="panel loading">Carregando dados…</div>
    <div v-else-if="!dashboard && tab === 'dashboard'" class="panel data-empty-state" role="status">Os dados ainda não foram carregados. <button class="btn secondary" type="button" @click="refreshVisibleData">Atualizar dados</button></div>

    <section v-if="tab === 'dashboard' && dashboard">
      <header class="page-header"><div><span class="eyebrow">DASHBOARD / PERFORMANCE</span><h1>Visão geral<span class="title-accent">.</span></h1><p>Uma visão clara das vendas, do estoque e do que merece atenção.</p></div><button class="btn secondary" @click="openModal('finance')"><AppIcon name="chart" :size="17" /> Explorar relatórios</button></header>
      <div class="cards">
        <button type="button" class="metric metric-click" @click="openModal('finance')"><div class="metric-top"><small>Receita após descontos · 30 dias</small><span class="metric-icon green"><AppIcon name="money" /></span></div><b>{{ money(dashboard.summary.revenue) }}</b><span class="metric-detail">Ver detalhamento financeiro <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('finance')"><div class="metric-top"><small>Vendas realizadas · 30 dias</small><span class="metric-icon blue"><AppIcon name="cart" /></span></div><b>{{ dashboard.summary.sales_count }}</b><span class="metric-detail">Ticket médio {{ money(dashboard.summary.average_ticket) }} <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('critico')"><div class="metric-top"><small>Estoque crítico</small><span class="metric-icon orange"><AppIcon name="alert" /></span></div><b>{{ inventoryCount.critico }}</b><span class="metric-detail">Ver produtos para reposição <AppIcon name="arrow" :size="14" /></span></button>
        <button type="button" class="metric metric-click" @click="openModal('vencido')"><div class="metric-top"><small>Produtos vencidos</small><span class="metric-icon red"><AppIcon name="clock" /></span></div><b>{{ inventoryCount.vencido }}</b><span class="metric-detail">{{ inventoryCount.a_vencer }} próximos do vencimento <AppIcon name="arrow" :size="14" /></span></button>
      </div>
      <div class="dashboard-chart-toolbar panel">
        <div><span class="eyebrow">ANÁLISE GERENCIAL</span><h2>Explore os dados de vendas</h2><p>Acompanhe período e indicadores. Receita considera os descontos, mas não representa lucro.</p></div>
        <div class="chart-controls"><label>Período<select v-model="chartPeriod"><option value="7d">Últimos 7 dias</option><option value="30d">Últimos 30 dias</option><option value="90d">Últimos 90 dias</option><option value="12m">Últimos 12 meses</option></select></label><label>Indicador<select v-model="chartMetric"><option value="revenue">Receita (R$)</option><option value="quantity">Unidades vendidas</option></select></label><label>Agrupar<select v-model="chartGrouping"><option value="day">Por dia</option><option value="week">Por semana</option><option value="month">Por mês</option></select></label><small v-if="chartLoading" class="chart-refreshing">Atualizando gráficos…</small></div>
      </div>
      <div v-if="chartError && !dashboardReport" class="chart-connection-warning" role="status">As análises ainda não estão disponíveis. <button class="btn secondary" @click="refreshDashboardCharts({ force: true })">Atualizar gráficos</button></div>
      <div v-if="dashboardReport" class="chart-update-line"><span><AppIcon name="check" :size="14" /> Atualizado às {{ chartUpdatedAt }} <span v-if="chartLoading"> · Sincronizando…</span></span><button type="button" class="btn secondary chart-reload" :disabled="chartLoading" @click="refreshDashboardCharts({ force: true })"><AppIcon name="refresh" :size="15" /> Atualizar gráficos</button></div>
      <div v-if="chartLoading && !dashboardReport" class="panel">Carregando análises…</div>
      <template v-if="dashboardReport">
        <div class="insight-strip"><div><span>Unidades vendidas</span><strong>{{ summaryInsights.units }}</strong></div><div><span>Produtos diferentes vendidos</span><strong>{{ summaryInsights.activeItems }}</strong></div><div><span>Maior categoria no faturamento</span><strong>{{ summaryInsights.concentration }}%</strong><small>{{ summaryInsights.topCategory }}</small></div><div><span>Ticket médio do período</span><strong>{{ money(dashboardReport.summary.average_ticket) }}</strong></div></div>
        <div class="grid-2 dashboard-top">
          <article class="panel chart-panel"><div class="panel-heading"><div><span class="eyebrow">SÉRIE TEMPORAL</span><h2>Evolução das vendas</h2></div><span class="chart-type-label">Barras</span></div><DecisionChart :rows="trendRows" type="bar" :currency="chartMetric === 'revenue'" label="Evolução das vendas no período selecionado" /></article>
          <article class="panel chart-panel top-products-chart"><div class="panel-heading"><div><span class="eyebrow">RANKING</span><h2>Itens mais vendidos</h2></div><span class="chart-type-label">Top 10 · Rosca</span></div><DecisionChart :rows="rankedRows" type="donut" :currency="false" label="Dez produtos mais vendidos por quantidade" /><div class="top-product-list" aria-label="Ranking dos dez produtos mais vendidos" tabindex="0"><div v-for="(p, i) in rankedProducts" :key="p.id" class="rank-row"><span class="rank-index">{{ String(i + 1).padStart(2, '0') }}</span><strong>{{ p.name }}</strong><span class="quantity">{{ p.quantity }} un.</span></div></div></article>
        </div>
        <article class="panel chart-panel category-analysis"><div class="panel-heading"><div><span class="eyebrow">MIX COMERCIAL</span><h2>Participação por categoria</h2></div><span class="chart-type-label">Rosca</span></div><DecisionChart :rows="categoryRows" type="donut" :currency="chartMetric === 'revenue'" label="Distribuição das vendas por categoria" /></article>
      </template>
      <div class="grid-2">
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">AÇÃO RECOMENDADA</span><h2>Prioridades do negócio</h2></div><span class="count-pill">{{ dashboard.recommendations.length }} avisos</span></div><div v-if="!dashboard.recommendations.length" class="empty">Nenhuma pendência identificada.</div><div v-for="(r, i) in dashboard.recommendations.slice(0, 6)" :key="i" class="recommendation"><span :class="['priority', r.priority]">{{ r.priority }}</span><div><strong>{{ r.product }}</strong><p>{{ r.message }}</p><small>{{ r.reason }}</small></div></div></article>
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">CONTROLE DE ESTOQUE</span><h2>Acompanhe as situações</h2></div><AppIcon name="package" /></div><button class="overview-link" @click="openModal('critico')"><span class="overview-icon orange"><AppIcon name="alert" /></span><span><strong>Estoque no mínimo</strong><small>Itens com saldo abaixo ou igual ao mínimo</small></span><b>{{ inventoryCount.critico }}</b><AppIcon name="arrow" :size="16" /></button><button class="overview-link" @click="openModal('vencido')"><span class="overview-icon red"><AppIcon name="clock" /></span><span><strong>Itens vencidos</strong><small>Separe apenas as unidades vencidas</small></span><b>{{ inventoryCount.vencido }}</b><AppIcon name="arrow" :size="16" /></button><button class="overview-link" @click="openModal('a_vencer')"><span class="overview-icon blue"><AppIcon name="calendar" /></span><span><strong>Vencem em 15 dias</strong><small>Antecipe as decisões de reposição</small></span><b>{{ inventoryCount.a_vencer }}</b><AppIcon name="arrow" :size="16" /></button><button class="btn secondary full" style="margin-top:18px" @click="openInventory()">Consultar todo o estoque <AppIcon name="arrow" :size="16" /></button></article>
      </div>
    </section>

    <section v-if="tab === 'products'"><header class="page-header"><div><span class="eyebrow">CATÁLOGO / CADASTROS</span><h1>Produtos<span class="title-accent">.</span></h1><p>Cadastre e organize os itens de sua loja.</p></div><span class="header-count">{{ products.length }} itens cadastrados</span></header>
      <div class="grid-form"><div class="stack"><form class="panel" @submit.prevent="saveProduct"><div class="panel-heading"><div><span class="eyebrow">GESTÃO DO CATÁLOGO</span><h2>{{ productForm.id ? 'Editar produto' : 'Cadastrar produto' }}</h2></div><AppIcon name="products" /></div><label>Nome do produto<input v-model="productForm.name" required maxlength="150" placeholder="Ex.: Pote plástico 1 litro" /></label><div class="form-row"><label>Categoria<select v-model="productForm.category"><option value="">Sem categoria</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></label><label>SKU<input v-model="productForm.sku" maxlength="50" placeholder="Opcional" /></label></div><div class="form-row"><label>Preço de compra<NumericField v-model="productForm.purchase_price" label="preço de compra" :min="0" step="0.01" :button-step="1" required /></label><label>Preço de venda<NumericField v-model="productForm.sale_price" label="preço de venda" :min="0" step="0.01" :button-step="1" required /></label></div><div class="form-row"><label>Saldo inicial / atual<NumericField v-model="productForm.stock" label="saldo de estoque" :min="0" required :disabled="Boolean(productForm.id && productForm.perishable)" /><small v-if="productForm.id && productForm.perishable" class="help-text">Para receber mais unidades, vá a Movimentações e informe a validade.</small></label><label>Estoque mínimo<NumericField v-model="productForm.minimum_stock" label="estoque mínimo" :min="0" required /></label></div><label class="check-label"><input v-model="productForm.perishable" type="checkbox" /> Produto perecível (controlar validade por lote)</label><label>{{ productForm.perishable ? 'Validade do saldo inicial / legado' : 'Validade (se aplicável)' }}<input v-model="productForm.expiration_date" type="date" :required="productForm.perishable && Number(productForm.stock) > 0 && !productForm.id" /></label><label class="check-label"><input v-model="productForm.active" type="checkbox" /> Produto ativo</label>
            <div class="product-photo-editor">
              <div class="photo-preview">
                <img v-if="photoPreviewUrl" :src="photoPreviewUrl" alt="Prévia da nova fotografia do produto" />
                <ProductThumbnail v-else :product-id="productForm.id" :updated-at="removePhoto ? null : productForm.image_updated_at" :name="productForm.name" size="editor" />
              </div>
              <div class="photo-editor-actions">
                <strong>Foto do produto <span class="photo-optional">(opcional)</span></strong>
                <small>JPEG padronizado automaticamente em 800 × 800 px ou menos, até 100 KB. Foto e galeria.</small>
                <div class="photo-buttons">
                  <button type="button" class="btn secondary" :disabled="busy || photoBusy" @click="photoGalleryInput?.click()">Escolher da galeria</button>
                  <button type="button" class="btn secondary" :disabled="busy || photoBusy" @click="photoCameraInput?.click()">Tirar foto</button>
                  <button v-if="productPhoto || (productForm.id && productForm.has_image && !removePhoto)" type="button" class="btn photo-remove" :disabled="busy || photoBusy" @click="discardPhoto">Remover foto</button>
                </div>
                <input ref="photoGalleryInput" class="visually-hidden-input" type="file" accept="image/*" aria-label="Selecionar imagem na galeria" @change="selectPhoto" />
                <input ref="photoCameraInput" class="visually-hidden-input" type="file" accept="image/*" capture="environment" aria-label="Fotografar produto" @change="selectPhoto" />
                <small v-if="productPhoto" class="photo-ready">Pronta: {{ productPhoto.name }} · {{ (productPhoto.size / 1024).toFixed(1) }} KB</small>
                <small v-if="photoBusy">Preparando e compactando imagem…</small>
                <small v-if="removePhoto && !productPhoto">A foto atual será removida ao salvar.</small>
                <p v-if="photoError" class="photo-error" role="alert">{{ photoError }}</p>
              </div>
            </div><div class="form-actions"><button class="btn primary" type="submit" :disabled="busy || photoBusy"><AppIcon :name="productForm.id ? 'check' : 'add'" :size="16" />{{ busy ? 'Salvando…' : productForm.id ? 'Salvar alterações' : 'Cadastrar produto' }}</button><button v-if="productForm.id" class="btn secondary" type="button" @click="resetProduct">Cancelar</button></div><p class="help-text">Para entradas e saídas de estoque use Movimentações: cada ajuste fica registrado.</p></form><form class="panel" @submit.prevent="addCategory"><div class="panel-heading"><h2>Nova categoria</h2></div><label>Nome<input v-model="categoryName" maxlength="100" required placeholder="Ex.: Utilidades domésticas" /></label><button type="submit" class="btn secondary" :disabled="busy"><AppIcon name="add" :size="16" />{{ busy ? 'Salvando…' : 'Adicionar categoria' }}</button></form></div>
      <article class="panel catalog"><div class="panel-heading"><div><span class="eyebrow">PRODUTOS CADASTRADOS</span><h2>Catálogo</h2></div><span class="count-pill">{{ visibleProducts.length }} resultados</span></div><div class="filters"><label class="search-input"><AppIcon name="search" :size="17" /><input v-model="search" type="search" placeholder="Buscar por produto, SKU ou categoria" aria-label="Pesquisar produtos" /></label><select v-model="filter" aria-label="Situação"><option value="all">Todos</option><option value="active">Ativos</option><option value="low">Estoque crítico</option><option value="inactive">Inativos</option></select></div><div v-if="!visibleProducts.length" class="empty">Nenhum produto encontrado.</div><div v-for="p in visibleProducts" :key="p.id" class="catalog-item"><ProductThumbnail :product-id="p.id" :updated-at="p.image_updated_at" :name="p.name" /><div class="product-info"><strong>{{ p.name }}</strong><small>{{ p.category_name || 'Sem categoria' }} · {{ p.sku || 'Sem SKU' }}</small><span :class="['tag', !p.active ? 'muted-tag' : p.stock <= p.minimum_stock ? 'warning-tag' : 'ok-tag']">{{ !p.active ? 'Inativo' : p.stock <= p.minimum_stock ? 'Reposição' : 'Disponível' }}</span></div><div class="product-pricing"><strong>{{ money(p.sale_price) }}</strong><small>{{ p.stock }} unidades</small><div class="inline-actions"><button @click="editProduct(p)"><AppIcon name="edit" :size="14" /> Editar</button><button :disabled="busy" @click="toggleProduct(p)">{{ p.active ? 'Desativar' : 'Ativar' }}</button><button class="danger-text" :disabled="busy" @click="deleteProduct(p)"><AppIcon name="trash" :size="14" /></button></div></div></div></article></div>
    </section>

    <section v-if="tab === 'sales'">
      <header class="page-header"><div><span class="eyebrow">PDV / OPERAÇÕES</span><h1>Nova venda<span class="title-accent">.</span></h1><p>Selecione o produto no campo fixo e acompanhe o carrinho logo abaixo.</p></div><button class="btn secondary" @click="openModal('finance')"><AppIcon name="chart" :size="16" /> Relatórios</button></header>
      <div class="grid-2 sale-layout">
        <form class="panel sale-panel" @submit.prevent="registerSale">
          <div class="panel-heading"><div><span class="eyebrow">PONTO DE VENDA</span><h2>Adicionar item</h2></div><AppIcon name="cart" /></div>
          <div class="sale-draft">
            <div class="sale-draft-controls">
              <div class="sale-product-field">
                <label for="sale-search">Produto</label>
                <div :class="['search-input', 'sale-search-box', { 'is-selected': saleDraft.product }]">
                  <AppIcon :name="saleDraft.product ? 'check' : 'search'" :size="19" />
                  <input id="sale-search" ref="saleSearchInput" v-model="saleDraft.query" type="text" autocomplete="off" placeholder="Buscar produto..." @focus="showSaleOptions" @click="showSaleOptions" @input="onSaleInput" @keydown.esc="saleSearchOpen = false" @blur="hideSaleOptions" role="combobox" aria-controls="sale-product-options" aria-autocomplete="list" aria-haspopup="listbox" :aria-expanded="saleSearchOpen" />
                  <button v-if="saleDraft.query" class="sale-search-action" type="button" aria-label="Limpar produto selecionado" @mousedown.prevent @click="clearSaleSearch"><AppIcon name="close" :size="16" /></button>
                  <button v-else type="button" class="sale-search-action" :aria-label="saleSearchOpen ? 'Fechar lista' : 'Mostrar produtos'" @mousedown.prevent @click="toggleSaleOptions"><AppIcon name="chevron" :size="17" /></button>
                </div>
              </div>
              <label class="qty-label">Quantidade<NumericField v-model="saleDraft.quantity" label="quantidade do produto" :min="1" :max="products.find(p => p.id === Number(saleDraft.product))?.available_stock ?? products.find(p => p.id === Number(saleDraft.product))?.stock" /></label>
              <button type="button" class="btn primary sale-add-btn" :disabled="!saleDraft.product || !Number.isInteger(Number(saleDraft.quantity)) || Number(saleDraft.quantity) < 1" @click="addItem"><AppIcon name="add" :size="17" /> Incluir</button>
            </div>
            <div v-if="saleSearchOpen" id="sale-product-options" class="sale-results" role="listbox" aria-label="Produtos disponíveis">
              <div class="sale-results-heading"><span>{{ saleDraft.query ? 'Resultados da busca' : 'Produtos disponíveis · A–Z' }}</span><small>{{ saleChoices.length }} exibidos</small></div>
              <button v-for="p in saleChoices" :key="p.id" type="button" role="option" :aria-selected="saleDraft.product === p.id" @mousedown.prevent="chooseSaleItem(p)" @click="chooseSaleItem(p)">
                <span class="sale-choice-name"><strong>{{ p.name }}</strong><small>{{ p.sku || p.category_name || 'Sem categoria' }}</small></span>
                <span class="sale-choice-price"><strong>{{ money(p.sale_price) }}</strong><small>{{ p.available_stock ?? p.stock }} un. disponíveis</small></span>
              </button>
              <div v-if="!saleChoices.length" class="empty sale-results-empty">Nenhum produto encontrado.</div>
            </div>
          </div>
          <div class="cart-heading"><h3>Itens adicionados</h3><span class="count-pill">{{ saleForm.items.length }} itens</span></div>
          <div v-if="!saleForm.items.length" class="empty cart-empty">Nenhum item na venda. Escolha um produto acima para começar.</div>
          <div v-for="(item, index) in saleForm.items" :key="item.key" class="cart-line"><span class="rank-index">{{ String(index + 1).padStart(2, '0') }}</span><div class="cart-line-name"><strong>{{ products.find(p => p.id === Number(item.product))?.name }}</strong><small>{{ money(products.find(p => p.id === Number(item.product))?.sale_price) }} / un.</small></div><label class="qty-label">Qtd.<NumericField v-model="item.quantity" :label="`quantidade de ${products.find(p => p.id === Number(item.product))?.name || 'produto'}`" :min="1" :max="products.find(p => p.id === Number(item.product))?.available_stock ?? products.find(p => p.id === Number(item.product))?.stock" /></label><strong class="cart-price">{{ money(Number(products.find(p => p.id === Number(item.product))?.sale_price || 0) * item.quantity) }}</strong><button type="button" class="remove-item" aria-label="Remover item" @click="removeItem(index)"><AppIcon name="trash" :size="17" /></button></div>
          <div class="sale-total"><div><span>Subtotal</span><strong>{{ money(subtotal) }}</strong></div><label>Desconto (R$)<NumericField v-model="saleForm.discount" label="desconto em reais" :min="0" :max="subtotal" step="0.01" :button-step="1" /></label><div class="grand-total"><span>Total da venda</span><strong>{{ money(total) }}</strong></div></div>
          <p v-if="saleForm.items.length && !cartValid" class="validation-hint">Confira quantidades, itens distintos e desconto.</p><button class="btn primary full" type="submit" :disabled="!cartValid || busy"><AppIcon name="check" :size="17" /> {{ busy ? 'Registrando…' : 'Finalizar venda' }}</button>
        </form>
        <article class="panel"><div class="panel-heading"><div><span class="eyebrow">REGISTROS</span><h2>Últimas vendas</h2></div><span class="count-pill">{{ sales.length }}</span></div><div v-if="!sales.length" class="empty">Ainda não existem vendas registradas.</div><div v-for="sale in sales.slice(0, 20)" :key="sale.id" class="detail-row sale-history-row"><div class="sale-history-main"><strong>Venda #{{ sale.id }} <span v-if="sale.canceled_at" class="tag muted-tag">Estornada</span></strong><small>{{ dateTime(sale.created_at) }} · {{ sale.items.length }} item(ns)</small><small v-if="sale.canceled_at">Estornada em {{ dateTime(sale.canceled_at) }} · {{ sale.cancellation_reason }}</small></div><div class="sale-history-actions"><strong :class="sale.canceled_at ? 'muted-price' : 'green-text'">{{ money(sale.total) }}</strong><button v-if="!sale.canceled_at" type="button" class="small-action reverse-sale-action" :disabled="busy" :aria-label="`Estornar venda número ${sale.id}`" @click="openReversal(sale)"><AppIcon name="undo" :size="15" /> Estornar</button><small v-else class="refund-recorded">Reembolso {{ money(sale.refunded_amount) }}</small></div></div></article>
      </div>
    </section>

    <section v-if="tab === 'inventory'"><header class="page-header"><div><span class="eyebrow">ESTOQUE / POSIÇÃO ATUAL</span><h1>Meu estoque<span class="title-accent">.</span></h1><p>Consulte o saldo, a situação de cada item e o valor investido em mercadorias.</p></div><button class="btn secondary" @click="exportXlsx('stock')"><AppIcon name="download" :size="17" /> Exportar Excel</button></header>
      <div class="inventory-kpis"><button class="inventory-kpi" @click="stockFilter = 'all'"><span><AppIcon name="layers" /></span><small>Produtos ativos</small><b>{{ stockOverview?.summary.products ?? inventoryCount.all }}</b></button><button class="inventory-kpi" @click="stockFilter = 'critico'"><span class="orange-text"><AppIcon name="alert" /></span><small>Estoque crítico</small><b>{{ inventoryCount.critico }}</b></button><button class="inventory-kpi" @click="stockFilter = 'a_vencer'"><span class="blue-text"><AppIcon name="calendar" /></span><small>Próximos do vencimento</small><b>{{ inventoryCount.a_vencer }}</b></button><button class="inventory-kpi" @click="stockFilter = 'vencido'"><span class="red-text"><AppIcon name="clock" /></span><small>Vencidos</small><b>{{ inventoryCount.vencido }}</b></button><div class="inventory-kpi inventory-total"><small>Valor estocado a custo</small><b>{{ money(stockOverview?.summary.inventory_value || 0) }}</b><small>{{ stockOverview?.summary.available_units ?? stockOverview?.summary.units ?? 0 }} disponíveis · {{ stockOverview?.summary.units ?? 0 }} físicas</small><small v-if="stockOverview?.summary.expired_stock_value">{{ money(stockOverview.summary.expired_stock_value) }} em mercadorias vencidas (a custo)</small></div></div>
      <article class="panel"><div class="panel-heading"><div><span class="eyebrow">INVENTÁRIO VISUAL</span><h2>Posição dos produtos</h2></div><span class="count-pill">{{ inventoryProducts.length }} resultados</span></div><div class="stock-filters"><label class="search-input"><AppIcon name="search" :size="17" /><input v-model="stockSearch" type="search" placeholder="Pesquisar nome, SKU ou categoria..." aria-label="Pesquisar estoque" /></label><select v-model="stockCategory" aria-label="Filtrar categoria"><option value="">Todas as categorias</option><option v-for="c in categories" :key="c.id" :value="String(c.id)">{{ c.name }}</option></select><select v-model="stockFilter" aria-label="Filtrar situação"><option value="all">Todas as situações</option><option value="normal">Em dia</option><option value="critico">Crítico</option><option value="a_vencer">A vencer</option><option value="vencido">Vencido</option><option value="inativo">Inativo</option></select></div><div v-if="!inventoryProducts.length" class="empty">Nenhum item corresponde aos filtros.</div><div v-else class="inventory-table-wrap"><table class="inventory-table"><thead><tr><th>Produto / SKU</th><th>Categoria</th><th>Saldo</th><th>Nível de estoque</th><th>Valor a custo</th><th>Situação</th><th></th></tr></thead><tbody><tr v-for="p in inventoryProducts" :key="p.id"><td><div class="item-cell"><span class="product-avatar"><AppIcon name="package" :size="17" /></span><div><strong>{{ p.name }}</strong><small>{{ p.sku || 'Sem SKU' }}</small></div></div></td><td>{{ p.category_name || 'Sem categoria' }}</td><td><strong>{{ p.stock }}</strong><small class="table-sub">Disponível: {{ p.available_stock ?? p.stock }}</small><small class="table-sub">Mín. {{ p.minimum_stock }}</small><small v-if="p.expired_units" class="table-sub negative">Vencido: {{ p.expired_units }}</small></td><td><div class="stock-progress"><div :class="{ 'progress-warning': Number(p.available_stock ?? p.stock) <= p.minimum_stock }" :style="{ width: `${Math.max(0, Math.min(100, (Number(p.available_stock ?? p.stock) / Math.max(1, p.minimum_stock * 2)) * 100))}%` }"></div></div></td><td>{{ money(Number(p.purchase_price) * p.stock) }}</td><td><span :class="['tag', inventoryStatus(p, today) === 'normal' ? 'ok-tag' : inventoryStatus(p, today) === 'critico' ? 'warning-tag' : inventoryStatus(p, today) === 'inativo' ? 'muted-tag' : 'danger-tag']">{{ labelStatus(p) }}</span></td><td><button class="small-action" @click="stockProduct = p.id; tab = 'movements'"><AppIcon name="arrows" :size="16" /> Ajustar</button></td></tr></tbody></table></div></article>
    </section>

    <section v-if="tab === 'movements'"><header class="page-header"><div><span class="eyebrow">ESTOQUE / RASTREABILIDADE</span><h1>Movimentações<span class="title-accent">.</span></h1><p>Registre entradas e saídas com justificativa. Consulte o histórico detalhado.</p></div><button class="btn secondary" @click="openInventory()"><AppIcon name="package" :size="16" /> Ver estoque</button></header><div class="grid-form"><form class="panel" @submit.prevent="adjustStock"><div class="panel-heading"><div><span class="eyebrow">ENTRADA / SAÍDA</span><h2>Ajustar saldo</h2></div><AppIcon name="arrows" /></div><label>Produto<select v-model="stockProduct" required><option value="">Selecione um produto</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} · {{ p.stock }} un.</option></select></label><label>Quantidade (positiva = entrada; negativa = saída)<NumericField v-model="stockDelta" label="ajuste de estoque" required /></label><label>Justificativa<select v-model="stockReason" required><option v-for="r in MOVEMENT_REASONS" :key="r.value" :value="r.value" :disabled="r.direction !== 'both' && r.direction !== (Number(stockDelta) > 0 ? 'in' : 'out')">{{ r.label }}</option></select></label><label v-if="stockReason === 'outro' || stockReason === 'inventario' || stockCustomNote">{{ stockReason === 'outro' ? 'Descreva o motivo (obrigatório)' : 'Detalhes adicionais (opcional)' }}<input v-model="stockCustomNote" maxlength="180" :required="stockReason === 'outro'" placeholder="Explique o ocorrido..." /></label><label v-if="showingReceiptExpiry">Nova validade do lote<input v-model="stockExpiry" type="date" required :min="localDateISO()" /><small>Essa validade será registrada apenas para as unidades recebidas, sem substituir os lotes anteriores.</small></label><p v-if="selectedMovementProduct?.perishable && Number(stockDelta) < 0" class="help-text">A baixa desconta primeiro o lote mais próximo do vencimento, incluindo lotes vencidos para descarte.</p><p v-if="!movementDirectionValid" class="validation-hint">A justificativa selecionada não corresponde ao sentido da movimentação.</p><button class="btn primary" type="submit" :disabled="busy || !movementFormValid"><AppIcon name="check" :size="17" /> {{ busy ? 'Salvando…' : 'Registrar movimentação' }}</button></form><article class="panel"><div class="panel-heading"><div><span class="eyebrow">AUDITORIA</span><h2>Histórico de estoque</h2></div><span class="count-pill">{{ filteredMovements.length }} registros</span></div><label>Filtrar por produto<select v-model="movementProduct"><option value="">Todos os produtos</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option></select></label><div v-if="!filteredMovements.length" class="empty">Nenhum movimento encontrado.</div><div v-for="m in filteredMovements.slice(0, 50)" :key="m.id" class="detail-row"><div><strong>{{ m.product_name }}</strong><small>{{ m.justification_display || m.reason_display }} · {{ m.note || 'Sem observação' }}</small><small>{{ m.stock_before }} → {{ m.stock_after }} un. · {{ dateTime(m.created_at) }}</small><small v-for="(lot, li) in m.lots" :key="li">Lote: {{ lot.quantity > 0 ? "+" : "" }}{{ lot.quantity }} un. · Validade {{ shortDate(lot.expiration_date) }}</small></div><span :class="['change-amount', m.delta > 0 ? 'positive' : 'negative']">{{ m.delta > 0 ? '+' : '' }}{{ m.delta }}</span></div></article></div></section>
    <footer class="app-footer" aria-label="Rodapé do Comercializa">
      <div class="footer-brand">
        <img :src="BRAND_ASSETS.horizontalOnLight" alt="Comercializa" class="footer-logo footer-logo-light" width="174" height="32" />
        <img :src="BRAND_ASSETS.horizontalOnDark" alt="Comercializa" class="footer-logo footer-logo-dark" width="174" height="32" />
      </div>
      <div class="footer-copy">
        <span>Desenvolvido por <strong>Arthur Azevêdo</strong></span>
        <small>© {{ copyrightYear }} Comercializa. Todos os direitos reservados.</small>
        <small class="app-version-mobile">Versão {{ APP_VERSION }}</small>
      </div>
    </footer>
  </main>

  <div v-if="modal" class="modal-backdrop" @click.self="closeModal"><section class="modal" role="dialog" aria-modal="true" :aria-label="modalTitles[modal]"><header class="modal-header"><div><span class="eyebrow">{{ modal === 'finance' ? 'RELATÓRIOS' : modal === 'sale-reversal' ? 'CANCELAMENTO / DEVOLUÇÃO' : 'ALERTAS DE ESTOQUE' }}</span><h2>{{ modalTitles[modal] }}</h2></div><button class="icon-btn" aria-label="Fechar janela" @click="closeModal"><AppIcon name="close" /></button></header>
    <template v-if="modal === 'finance'"><div class="modal-body"><p class="help-text" style="margin-bottom:18px">Receita após descontos (não equivale a lucro líquido). Filtre o intervalo e explore produtos e categorias.</p><form class="report-filters" @submit.prevent="refreshFinance"><label>Início<input v-model="reportFilters.start" type="date" required /></label><label>Fim<input v-model="reportFilters.end" type="date" required /></label><label>Categoria<select v-model="reportFilters.category"><option value="">Todas</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></label><label>Produto<select v-model="reportFilters.product"><option value="">Todos</option><option v-for="p in products.filter(p => !reportFilters.category || String(p.category) === String(reportFilters.category))" :key="p.id" :value="p.id">{{ p.name }}</option></select></label><button class="btn primary" type="submit" :disabled="financeLoading"><AppIcon name="filter" :size="16" /> {{ financeLoading ? 'Consultando…' : 'Aplicar' }}</button></form><div class="report-actions"><button type="button" class="btn secondary" @click="reportFilters = defaultReportFilters(); refreshFinance()">Mês atual</button><button type="button" class="btn secondary" @click="reportFilters = { ...reportFilters, start: `${new Date().getFullYear()}-01-01`, end: localDateISO() }; refreshFinance()">Ano atual</button><button class="btn secondary" @click="exportXlsx('finance')"><AppIcon name="download" :size="16" /> Exportar Excel</button></div><div v-if="financeError && !finance" class="report-unavailable" role="status">Relatório indisponível no momento. <button type="button" class="btn secondary" @click="refreshFinance">Tentar novamente</button></div><div v-if="finance" class="report-content"><div class="report-summary"><div><small>Receita após descontos</small><strong>{{ money(finance.summary.revenue) }}</strong></div><div><small>Vendas</small><strong>{{ finance.summary.sales_count }}</strong></div><div><small>Unidades vendidas</small><strong>{{ finance.summary.items_sold }}</strong></div><div><small>Ticket médio</small><strong>{{ money(finance.summary.average_ticket) }}</strong></div></div><div class="report-explanation">Bruto: {{ money(finance.summary.gross) }} · Descontos atribuídos: {{ money(finance.summary.discounts) }}. A análise considera somente os filtros aplicados.</div><div class="report-grid"><div><h3>Desempenho por categoria</h3><div v-if="!finance.categories.length" class="empty">Sem vendas neste período.</div><div v-for="c in finance.categories" :key="c.name" class="detail-row"><div><strong>{{ c.name }}</strong><small>{{ c.quantity }} unidades</small></div><b>{{ money(c.revenue) }}</b></div></div><div><h3>Produtos vendidos</h3><div v-if="!finance.products.length" class="empty">Sem itens vendidos.</div><div v-for="p in finance.products" :key="p.id" class="detail-row"><div><strong>{{ p.name }}</strong><small>{{ p.category }} · {{ p.quantity }} un.</small></div><b>{{ money(p.revenue) }}</b></div></div></div><h3 style="margin-top:24px">Evolução por dia</h3><div v-if="!finance.daily.length" class="empty">Nenhuma venda no período selecionado.</div><div v-for="d in finance.daily" :key="d.date" class="detail-row"><span>{{ shortDate(d.date) }}</span><span>{{ d.quantity }} unidades</span><strong>{{ money(d.revenue) }}</strong></div></div></div></template>
    <template v-else-if="modal === 'sale-reversal' && saleToReverse">
      <form class="reversal-form" @submit.prevent="confirmReversal">
        <div class="modal-body">
          <p class="help-text">O estorno é <strong>integral</strong>. Todos os produtos desta venda voltam ao estoque, preservando os lotes e o histórico original. A venda deixa de contar nos gráficos e relatórios.</p>
          <div class="reversal-summary"><span>Venda #{{ saleToReverse.id }}</span><strong>{{ money(saleToReverse.total) }}</strong><small>Valor de reembolso a registrar</small></div>
          <label>Motivo do estorno<select v-model="reversalReason" required><option v-for="reason in reversalReasons" :key="reason" :value="reason">{{ reason }}</option></select></label>
          <label v-if="reversalReason === 'Outro motivo'">Descreva o motivo<input v-model="reversalDetails" required minlength="3" maxlength="255" placeholder="Motivo do estorno" /></label>
          <p class="reversal-notice"><AppIcon name="info" :size="17" /> O sistema registra o valor devolvido na contabilidade da venda, mas não transfere dinheiro automaticamente ao cliente. Faça o reembolso no meio de pagamento utilizado.</p>
        </div>
        <footer class="modal-footer"><button type="button" class="btn secondary" @click="closeModal">Voltar</button><button class="btn danger" type="submit" :disabled="busy || !reversalValid"><AppIcon name="undo" :size="17" /> {{ busy ? 'Estornando…' : 'Confirmar estorno' }}</button></footer>
      </form>
    </template>
    <template v-else><div class="modal-body"><p class="help-text">{{ modal === 'critico' ? 'Produtos ativos com saldo igual ou inferior ao estoque mínimo, inclusive itens com validade comprometida.' : modal === 'vencido' ? 'Produtos ativos com saldo disponível e validade já ultrapassada.' : 'Produtos ativos que vencem nos próximos 15 dias, incluindo hoje.' }}</p><div v-if="!modalItems.length" class="empty">Nenhum produto nesta situação.</div><div v-for="p in modalItems" :key="p.id" class="modal-product"><span class="product-avatar"><AppIcon name="package" /></span><div><strong>{{ p.name }}</strong><small>{{ p.category_name || 'Sem categoria' }} · {{ p.sku || 'Sem SKU' }}</small><small v-if="p.nearest_expiration || p.expiration_date">Validade mais próxima: {{ shortDate(p.nearest_expiration || p.expiration_date) }}</small></div><div class="modal-product-end"><b>{{ p.stock }} un.</b><small>Vendável: {{ p.available_stock ?? p.stock }}</small><small>Mínimo: {{ p.minimum_stock }}</small></div></div></div><footer class="modal-footer"><button class="btn secondary" @click="closeModal">Fechar</button><button class="btn primary" @click="openInventory(modal)">Ver na tela de estoque <AppIcon name="arrow" :size="15" /></button></footer></template>
  </section></div>
</div>
</template>
