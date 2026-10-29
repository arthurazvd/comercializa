<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from './api'
import { formatMoney, localDateISO, eligibleProducts, calculateCart, validCart } from './utils'

const tab = ref('dashboard')
const products = ref([])
const categories = ref([])
const dashboard = ref(null)
const sales = ref([])
const movements = ref([])
const message = ref('')
const messageType = ref('success')
const busy = ref(false)
const loading = ref(true)
const search = ref('')
const filter = ref('all')
const stockNote = ref('')
const stockProduct = ref('')
const stockDelta = ref(1)
const categoryName = ref('')

const blankProduct = () => ({
  id: null, name: '', category: '', sku: '', purchase_price: 0,
  sale_price: 0, stock: 0, minimum_stock: 0, expiration_date: '', active: true,
})
const productForm = ref(blankProduct())
const saleForm = ref({ items: [{ product: '', quantity: 1 }], discount: 0 })

const today = localDateISO()
const availableProducts = computed(() => eligibleProducts(products.value, today))
const visibleProducts = computed(() => products.value.filter(p => {
  const term = search.value.trim().toLocaleLowerCase('pt-BR')
  const matchTerm = !term || [p.name, p.sku, p.category_name].some(
    v => String(v ?? '').toLocaleLowerCase('pt-BR').includes(term),
  )
  const matchFilter = filter.value === 'all' || (filter.value === 'active' && p.active)
    || (filter.value === 'low' && p.active && p.stock <= p.minimum_stock)
    || (filter.value === 'inactive' && !p.active)
  return matchTerm && matchFilter
}))
const subtotal = computed(() => calculateCart(saleForm.value.items, products.value).subtotal)
const total = computed(() => calculateCart(saleForm.value.items, products.value, saleForm.value.discount).total)
const cartValid = computed(() => validCart(saleForm.value.items, products.value, saleForm.value.discount, today))
const money = formatMoney

function alertUser(text, type = 'success') {
  message.value = text
  messageType.value = type
}
function errorText(error) {
  const data = error?.response?.data
  if (!data) return 'Não foi possível conectar à API. Verifique se o backend está ativo.'
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  return Object.entries(data).map(([field, errors]) => `${field}: ${
    Array.isArray(errors) ? errors.join(', ') : typeof errors === 'object' ? JSON.stringify(errors) : errors
  }`).join(' · ')
}
async function loadAll() {
  loading.value = true
  try {
    const [p, c, d, s, m] = await Promise.all([
      api.get('products/'), api.get('categories/'), api.get('dashboard/'),
      api.get('sales/'), api.get('stock-movements/'),
    ])
    products.value = p.data
    categories.value = c.data
    dashboard.value = d.data
    sales.value = s.data
    movements.value = m.data
  } catch (error) {
    alertUser(errorText(error), 'error')
  } finally {
    loading.value = false
  }
}
function resetProduct() { productForm.value = blankProduct() }
function editProduct(product) {
  productForm.value = { ...product, category: product.category ?? '', expiration_date: product.expiration_date ?? '' }
  tab.value = 'products'
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
async function saveProduct() {
  if (busy.value) return
  busy.value = true
  try {
    const payload = {
      ...productForm.value, category: productForm.value.category || null,
      sku: productForm.value.sku || null, expiration_date: productForm.value.expiration_date || null,
    }
    if (payload.id) {
      await api.put(`products/${payload.id}/`, payload)
      alertUser('Produto atualizado com sucesso.')
    } else {
      await api.post('products/', payload)
      alertUser('Produto cadastrado com sucesso.')
    }
    resetProduct()
    await loadAll()
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function toggleProduct(product) {
  if (busy.value) return
  busy.value = true
  try {
    await api.patch(`products/${product.id}/`, { active: !product.active })
    await loadAll()
    alertUser(product.active ? 'Produto desativado. Seu histórico foi preservado.' : 'Produto reativado.')
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function deleteProduct(product) {
  if (!window.confirm(`Excluir "${product.name}"? Produtos com histórico devem ser desativados.`)) return
  try {
    await api.delete(`products/${product.id}/`)
    await loadAll()
    alertUser('Produto excluído.')
  } catch (error) { alertUser(errorText(error), 'error') }
}
async function addCategory() {
  if (!categoryName.value.trim()) return
  try {
    await api.post('categories/', { name: categoryName.value.trim() })
    categoryName.value = ''
    await loadAll()
    alertUser('Categoria cadastrada.')
  } catch (error) { alertUser(errorText(error), 'error') }
}
function addItem() { saleForm.value.items.push({ product: '', quantity: 1 }) }
function removeItem(index) {
  if (saleForm.value.items.length > 1) saleForm.value.items.splice(index, 1)
}
async function registerSale() {
  if (!cartValid.value || busy.value) return
  busy.value = true
  try {
    await api.post('sales/', {
      discount: Number(saleForm.value.discount) || 0,
      items: saleForm.value.items.map(item => ({ product: Number(item.product), quantity: Number(item.quantity) })),
    })
    saleForm.value = { items: [{ product: '', quantity: 1 }], discount: 0 }
    await loadAll()
    alertUser('Venda registrada: estoque e indicadores atualizados.')
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
async function adjustStock() {
  if (busy.value || !stockProduct.value || !Number.isInteger(Number(stockDelta.value)) || !Number(stockDelta.value)) return
  busy.value = true
  try {
    await api.post('stock-movements/', {
      product: Number(stockProduct.value), delta: Number(stockDelta.value), note: stockNote.value,
    })
    stockDelta.value = 1
    stockNote.value = ''
    await loadAll()
    alertUser('Movimentação registrada no histórico de estoque.')
  } catch (error) { alertUser(errorText(error), 'error') }
  finally { busy.value = false }
}
function date(value) { return value ? new Date(value).toLocaleString('pt-BR') : '—' }
function shortDate(value) { return value ? value.substring(8, 10) + '/' + value.substring(5, 7) : '—' }
const maxRevenue = computed(() => Math.max(1, ...((dashboard.value?.daily_revenue || []).map(d => Number(d.revenue)))))

onMounted(loadAll)
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand"><span class="brand-mark">C<span class="brand-dot">.</span></span><div><strong>comercializa</strong><small>WORKSPACE</small></div></div>
      <div class="sidebar-label">NAVEGAÇÃO</div>
      <nav aria-label="Menu principal">
        <button :class="{ active: tab === 'dashboard' }" @click="tab = 'dashboard'"><span>▦</span> Visão geral</button>
        <button :class="{ active: tab === 'products' }" @click="tab = 'products'"><span>▤</span> Produtos</button>
        <button :class="{ active: tab === 'sales' }" @click="tab = 'sales'"><span>◈</span> Vendas</button>
        <button :class="{ active: tab === 'stock' }" @click="tab = 'stock'"><span>⇄</span> Estoque</button>
      </nav>
      <div class="sidebar-footer"><span class="status-dot"></span> Gestão e inteligência <small>Versão de desenvolvimento</small></div>
    </aside>

    <main class="main-content">
      <div class="topbar"><span>COMERCIALIZA <span class="crumb">/ {{ { dashboard: 'Visão geral', products: 'Produtos', sales: 'Vendas', stock: 'Estoque' }[tab] }}</span></span><span class="topbar-right"><span class="status-dot"></span> Sistema de gestão</span></div>
      <div v-if="message" :class="['notice', messageType]" role="status"><span>{{ message }}</span><button aria-label="Fechar aviso" @click="message = ''">×</button></div>
      <div v-if="loading && !dashboard" class="panel loading">Carregando informações do sistema…</div>

      <section v-if="tab === 'dashboard' && dashboard">
        <header class="page-header"><div><div class="eyebrow">PAINEL DE INTELIGÊNCIA</div><h1>Visão geral <span class="title-accent">.</span></h1><p>Acompanhe o desempenho e antecipe decisões no seu negócio.</p></div><button class="btn secondary" @click="loadAll">↻ Atualizar dados</button></header>
        <div class="cards">
          <article class="metric"><div class="metric-top"><small>Receita líquida · 30 dias</small><span class="metric-icon green">↗</span></div><b>{{ money(dashboard.summary.revenue) }}</b><span class="metric-detail">Descontos: {{ money(dashboard.summary.discounts) }}</span></article>
          <article class="metric"><div class="metric-top"><small>Vendas realizadas</small><span class="metric-icon blue">◈</span></div><b>{{ dashboard.summary.sales_count }}</b><span class="metric-detail">Ticket médio: {{ money(dashboard.summary.average_ticket) }}</span></article>
          <article class="metric"><div class="metric-top"><small>Estoque crítico</small><span class="metric-icon orange">!</span></div><b>{{ dashboard.summary.low_stock_count }}</b><span class="metric-detail">Produtos para reposição</span></article>
          <article class="metric"><div class="metric-top"><small>Produtos vencidos</small><span class="metric-icon red">×</span></div><b>{{ dashboard.summary.expired_count }}</b><span class="metric-detail">{{ dashboard.summary.expiring_count }} próximos do vencimento</span></article>
        </div>
        <div class="grid-2 dashboard-top">
          <article class="panel"><div class="panel-heading"><div><span class="eyebrow">ANÁLISE DE RESULTADOS</span><h2>Vendas dos últimos 7 dias</h2></div><span class="text-muted">Receita líquida</span></div>
            <div class="chart" role="img" aria-label="Gráfico da receita diária dos últimos sete dias"><div v-for="point in dashboard.daily_revenue" :key="point.date" class="bar-column"><strong>{{ Number(point.revenue) ? money(point.revenue) : '—' }}</strong><div class="bar-track"><div class="bar-fill" :style="{ height: `${Math.max(2, Number(point.revenue) / maxRevenue * 100)}%` }"></div></div><small>{{ shortDate(point.date) }}</small></div></div>
          </article>
          <article class="panel"><div class="panel-heading"><div><span class="eyebrow">PRODUTOS</span><h2>Mais vendidos</h2></div><span class="text-muted">30 dias</span></div><div v-if="!dashboard.top_products.length" class="empty">Registre vendas para visualizar o ranking.</div><div v-for="(p, i) in dashboard.top_products" :key="p.product_id" class="rank-row"><span class="rank-index">{{ String(i + 1).padStart(2, '0') }}</span><strong>{{ p.product__name }}</strong><span class="quantity">{{ p.quantity_sold }} un.</span></div></article>
        </div>
        <div class="grid-2">
          <article class="panel"><div class="panel-heading"><div><span class="eyebrow">PRIORIDADES</span><h2>Recomendações inteligentes</h2></div><span class="count-pill">{{ dashboard.recommendations.length }} alertas</span></div><div v-if="!dashboard.recommendations.length" class="empty">Nenhuma recomendação no momento.</div><div v-for="(r, i) in dashboard.recommendations.slice(0, 8)" :key="`${r.type}-${r.product_id}-${i}`" class="recommendation"><span :class="['priority', r.priority]">{{ r.priority }}</span><div><strong>{{ r.product }}</strong><p>{{ r.message }}</p><small>{{ r.reason }}</small></div></div></article>
          <article class="panel"><div class="panel-heading"><div><span class="eyebrow">ATENÇÃO OPERACIONAL</span><h2>Estoque e validade</h2></div></div><div v-if="!dashboard.low_stock.length && !dashboard.expired.length" class="empty">Nenhum alerta de estoque.</div><div v-for="p in dashboard.expired.slice(0, 5)" :key="`expired-${p.id}`" class="detail-row"><span><strong>{{ p.name }}</strong><small>Vencido em {{ shortDate(p.expiration_date) }}</small></span><span class="tag danger-tag">Vencido</span></div><div v-for="p in dashboard.low_stock.slice(0, 6)" :key="`low-${p.id}`" class="detail-row"><span><strong>{{ p.name }}</strong><small>Estoque mínimo: {{ p.minimum_stock }}</small></span><span class="tag warning-tag">{{ p.stock }} un.</span></div></article>
        </div>
      </section>

      <section v-if="tab === 'products'"><header class="page-header"><div><div class="eyebrow">CADASTRO E GESTÃO</div><h1>Produtos <span class="title-accent">.</span></h1><p>Organize seu catálogo e mantenha os dados sempre atualizados.</p></div><span class="header-count">{{ products.length }} cadastrados</span></header>
        <div class="grid-form"><div class="stack"><form class="panel" @submit.prevent="saveProduct"><div class="panel-heading"><div><span class="eyebrow">CADASTRO</span><h2>{{ productForm.id ? 'Editar produto' : 'Novo produto' }}</h2></div></div><label>Nome do produto <input v-model="productForm.name" required maxlength="150" placeholder="Ex.: Café torrado 500 g" /></label><div class="form-row"><label>Categoria<select v-model="productForm.category"><option value="">Sem categoria</option><option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option></select></label><label>Código SKU<input v-model="productForm.sku" maxlength="50" placeholder="Opcional" /></label></div><div class="form-row"><label>Preço de compra<input v-model.number="productForm.purchase_price" type="number" step="0.01" min="0" required /></label><label>Preço de venda<input v-model.number="productForm.sale_price" type="number" step="0.01" min="0" required /></label></div><div class="form-row"><label>Estoque atual<input v-model.number="productForm.stock" type="number" step="1" min="0" required /></label><label>Estoque mínimo<input v-model.number="productForm.minimum_stock" type="number" step="1" min="0" required /></label></div><label>Data de validade<input v-model="productForm.expiration_date" type="date" /></label><label class="check-label"><input v-model="productForm.active" type="checkbox" /> Produto ativo</label><div class="form-actions"><button class="btn primary" type="submit" :disabled="busy">{{ busy ? 'Salvando…' : productForm.id ? 'Salvar alterações' : '+ Cadastrar produto' }}</button><button v-if="productForm.id" class="btn secondary" type="button" @click="resetProduct">Cancelar</button></div></form><form class="panel" @submit.prevent="addCategory"><div class="panel-heading"><h2>Nova categoria</h2></div><label>Nome<input v-model="categoryName" maxlength="100" required placeholder="Nome da categoria" /></label><button type="submit" class="btn secondary">Adicionar categoria</button></form></div>
          <article class="panel catalog"><div class="panel-heading"><div><span class="eyebrow">CATÁLOGO</span><h2>Produtos cadastrados</h2></div><span class="count-pill">{{ visibleProducts.length }} resultados</span></div><div class="filters"><input v-model="search" type="search" placeholder="Buscar por nome, SKU ou categoria…" aria-label="Pesquisar produtos" /><select v-model="filter" aria-label="Filtrar produtos"><option value="all">Todos</option><option value="active">Ativos</option><option value="low">Estoque baixo</option><option value="inactive">Inativos</option></select></div><div v-if="!visibleProducts.length" class="empty">Nenhum produto encontrado.</div><div v-for="p in visibleProducts" :key="p.id" class="catalog-item"><div class="product-avatar">{{ p.name.charAt(0).toUpperCase() }}</div><div class="product-info"><strong>{{ p.name }}</strong><small>{{ p.category_name || 'Sem categoria' }} · SKU {{ p.sku || '—' }}</small><span :class="['tag', !p.active ? 'muted-tag' : p.stock <= p.minimum_stock ? 'warning-tag' : 'ok-tag']">{{ !p.active ? 'Inativo' : p.stock <= p.minimum_stock ? 'Estoque baixo' : 'Disponível' }}</span></div><div class="product-pricing"><strong>{{ money(p.sale_price) }}</strong><small>{{ p.stock }} un. em estoque</small><div class="inline-actions"><button @click="editProduct(p)">Editar</button><button @click="toggleProduct(p)">{{ p.active ? 'Desativar' : 'Ativar' }}</button><button class="danger-text" @click="deleteProduct(p)">Excluir</button></div></div></div></article>
        </div></section>

      <section v-if="tab === 'sales'"><header class="page-header"><div><div class="eyebrow">FRENTE DE VENDAS</div><h1>Registrar venda <span class="title-accent">.</span></h1><p>Monte um carrinho com vários produtos e finalize em uma operação.</p></div></header><div class="grid-2 sale-layout"><form class="panel" @submit.prevent="registerSale"><div class="panel-heading"><div><span class="eyebrow">NOVA OPERAÇÃO</span><h2>Itens da venda</h2></div><button type="button" class="btn secondary" @click="addItem">+ Adicionar item</button></div><div v-for="(item, index) in saleForm.items" :key="index" class="cart-item"><div class="cart-item-number">{{ String(index + 1).padStart(2, '0') }}</div><label>Produto<select v-model="item.product" required><option value="">Selecione um produto</option><option v-for="p in availableProducts" :key="p.id" :value="p.id">{{ p.name }} · {{ money(p.sale_price) }} · {{ p.stock }} un.</option></select></label><label class="qty-label">Qtd.<input v-model.number="item.quantity" type="number" min="1" step="1" required :max="products.find(p => p.id === Number(item.product))?.stock" /></label><button type="button" class="remove-item" :disabled="saleForm.items.length === 1" aria-label="Remover item" @click="removeItem(index)">×</button></div><div class="sale-total"><div><span>Subtotal</span><strong>{{ money(subtotal) }}</strong></div><label>Desconto (R$)<input v-model.number="saleForm.discount" type="number" min="0" step="0.01" :max="subtotal" /></label><div class="grand-total"><span>Total da venda</span><strong>{{ money(total) }}</strong></div></div><p v-if="!cartValid" class="validation-hint">Selecione produtos diferentes, com quantidades disponíveis, e confira o desconto.</p><button class="btn primary full" type="submit" :disabled="!cartValid || busy">{{ busy ? 'Registrando…' : '✓ Finalizar venda' }}</button></form><article class="panel"><div class="panel-heading"><div><span class="eyebrow">HISTÓRICO</span><h2>Últimas vendas</h2></div><span class="count-pill">{{ sales.length }}</span></div><div v-if="!sales.length" class="empty">Ainda não existem vendas registradas.</div><div v-for="sale in sales.slice(0, 12)" :key="sale.id" class="detail-row"><div><strong>Venda #{{ sale.id }}</strong><small>{{ date(sale.created_at) }} · {{ sale.items.length }} item(ns)</small></div><strong class="green-text">{{ money(sale.total) }}</strong></div></article></div></section>

      <section v-if="tab === 'stock'"><header class="page-header"><div><div class="eyebrow">CONTROLE OPERACIONAL</div><h1>Movimentações <span class="title-accent">.</span></h1><p>Ajustes e saídas registrados com histórico de movimentação.</p></div></header><div class="grid-form"><form class="panel" @submit.prevent="adjustStock"><div class="panel-heading"><div><span class="eyebrow">AJUSTE MANUAL</span><h2>Movimentar estoque</h2></div></div><label>Produto<select v-model="stockProduct" required><option value="">Selecione um produto</option><option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }} · {{ p.stock }} un.</option></select></label><label>Quantidade (positiva para entrada; negativa para saída)<input v-model.number="stockDelta" type="number" step="1" required /></label><label>Justificativa<input v-model="stockNote" required maxlength="255" placeholder="Ex.: Recebimento, inventário, avaria…" /></label><button class="btn primary" type="submit" :disabled="busy || !stockProduct || !Number(stockDelta) || !stockNote.trim()">{{ busy ? 'Salvando…' : 'Registrar movimentação' }}</button></form><article class="panel"><div class="panel-heading"><div><span class="eyebrow">RASTREABILIDADE</span><h2>Histórico de estoque</h2></div><span class="count-pill">{{ movements.length }} registros</span></div><div v-if="!movements.length" class="empty">Nenhuma movimentação registrada.</div><div v-for="movement in movements.slice(0, 30)" :key="movement.id" class="detail-row"><div><strong>{{ movement.product_name }}</strong><small>{{ movement.reason_display }} · {{ movement.note || date(movement.created_at) }}</small><small>{{ movement.stock_before }} → {{ movement.stock_after }} un. · {{ date(movement.created_at) }}</small></div><span :class="['change-amount', movement.delta > 0 ? 'positive' : 'negative']">{{ movement.delta > 0 ? '+' : '' }}{{ movement.delta }}</span></div></article></div></section>
    </main>
  </div>
</template>
