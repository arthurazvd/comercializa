<script setup>
import { onMounted, ref } from 'vue'
import { api } from './api'

const tab = ref('dashboard')
const products = ref([])
const categories = ref([])
const dashboard = ref(null)
const sales = ref([])
const message = ref('')

const productForm = ref({
  id: null,
  name: '',
  category: '',
  sku: '',
  purchase_price: 0,
  sale_price: 0,
  stock: 0,
  minimum_stock: 0,
  expiration_date: '',
  active: true,
})

const saleForm = ref({
  product: '',
  quantity: 1,
  discount: 0,
})

async function loadAll() {
  const [p, c, d, s] = await Promise.all([
    api.get('products/'),
    api.get('categories/'),
    api.get('dashboard/'),
    api.get('sales/'),
  ])
  products.value = p.data
  categories.value = c.data
  dashboard.value = d.data
  sales.value = s.data
}

function resetProduct() {
  productForm.value = {
    id: null, name: '', category: '', sku: '',
    purchase_price: 0, sale_price: 0, stock: 0,
    minimum_stock: 0, expiration_date: '', active: true,
  }
}

function editProduct(p) {
  productForm.value = {
    ...p,
    category: p.category ?? '',
    expiration_date: p.expiration_date ?? '',
  }
  tab.value = 'products'
}

async function saveProduct() {
  message.value = ''
  const payload = {
    ...productForm.value,
    category: productForm.value.category || null,
    sku: productForm.value.sku || null,
    expiration_date: productForm.value.expiration_date || null,
  }

  if (payload.id) {
    await api.put(`products/${payload.id}/`, payload)
    message.value = 'Produto atualizado.'
  } else {
    await api.post('products/', payload)
    message.value = 'Produto cadastrado.'
  }
  resetProduct()
  await loadAll()
}

async function deleteProduct(id) {
  if (!confirm('Excluir este produto?')) return
  await api.delete(`products/${id}/`)
  await loadAll()
}

async function registerSale() {
  message.value = ''
  try {
    await api.post('sales/', {
      discount: saleForm.value.discount || 0,
      items: [{
        product: Number(saleForm.value.product),
        quantity: Number(saleForm.value.quantity),
      }],
    })
    message.value = 'Venda registrada e estoque atualizado.'
    saleForm.value = { product: '', quantity: 1, discount: 0 }
    await loadAll()
  } catch (error) {
    const data = error.response?.data
    message.value = typeof data === 'object' ? JSON.stringify(data) : 'Erro ao registrar venda.'
  }
}

function money(value) {
  return Number(value || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

onMounted(loadAll)
</script>

<template>
  <div class="layout">
    <aside>
      <div class="brand">
        <span class="brand-mark">C</span>
        <strong>Comercializa</strong>
      </div>
      <p class="subtitle">Gestão + Apoio à Decisão</p>

      <nav>
        <button :class="{ active: tab === 'dashboard' }" @click="tab = 'dashboard'">Visão gerencial</button>
        <button :class="{ active: tab === 'products' }" @click="tab = 'products'">Produtos</button>
        <button :class="{ active: tab === 'sales' }" @click="tab = 'sales'">Registrar venda</button>
      </nav>
    </aside>

    <main>
      <div v-if="message" class="message">{{ message }}</div>

      <section v-if="tab === 'dashboard' && dashboard">
        <header>
          <div>
            <span class="eyebrow">SAD</span>
            <h1>Visão gerencial</h1>
            <p>O sistema transforma vendas e estoque em alertas e recomendações.</p>
          </div>
        </header>

        <div class="cards">
          <article><small>Faturamento · 30 dias</small><b>{{ money(dashboard.summary.revenue) }}</b></article>
          <article><small>Vendas · 30 dias</small><b>{{ dashboard.summary.sales_count }}</b></article>
          <article><small>Estoque crítico</small><b>{{ dashboard.summary.low_stock_count }}</b></article>
          <article><small>Próximos do vencimento</small><b>{{ dashboard.summary.expiring_count }}</b></article>
        </div>

        <div class="grid-2">
          <article class="panel">
            <h2>Recomendações</h2>
            <div v-if="!dashboard.recommendations.length" class="empty">Nenhuma recomendação no momento.</div>
            <div v-for="r in dashboard.recommendations" :key="`${r.type}-${r.product_id}`" class="recommendation">
              <span :class="['badge', r.priority]">{{ r.priority }}</span>
              <div>
                <strong>{{ r.product }}</strong>
                <p>{{ r.message }}</p>
                <small>{{ r.reason }}</small>
              </div>
            </div>
          </article>

          <article class="panel">
            <h2>Mais vendidos</h2>
            <div v-if="!dashboard.top_products.length" class="empty">Registre vendas para gerar o ranking.</div>
            <div v-for="(p, index) in dashboard.top_products" :key="p.product_id" class="ranking">
              <span>#{{ index + 1 }}</span>
              <strong>{{ p.product__name }}</strong>
              <small>{{ p.quantity_sold }} un.</small>
            </div>
          </article>
        </div>

        <div class="grid-2">
          <article class="panel">
            <h2>Estoque crítico</h2>
            <div v-for="p in dashboard.low_stock" :key="p.id" class="row">
              <span>{{ p.name }}</span><strong>{{ p.stock }} / mín. {{ p.minimum_stock }}</strong>
            </div>
          </article>
          <article class="panel">
            <h2>Baixa movimentação</h2>
            <div v-for="p in dashboard.stagnant" :key="p.id" class="row">
              <span>{{ p.name }}</span><strong>{{ p.stock }} em estoque</strong>
            </div>
          </article>
        </div>
      </section>

      <section v-if="tab === 'products'">
        <header>
          <div>
            <span class="eyebrow">Base operacional</span>
            <h1>Produtos</h1>
            <p>Os dados cadastrados aqui alimentam as análises do SAD.</p>
          </div>
        </header>

        <div class="grid-form">
          <form class="panel" @submit.prevent="saveProduct">
            <h2>{{ productForm.id ? 'Editar produto' : 'Novo produto' }}</h2>
            <label>Nome<input v-model="productForm.name" required /></label>
            <label>Categoria
              <select v-model="productForm.category">
                <option value="">Sem categoria</option>
                <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
              </select>
            </label>
            <label>SKU<input v-model="productForm.sku" /></label>
            <div class="form-row">
              <label>Preço de compra<input v-model.number="productForm.purchase_price" type="number" step="0.01" min="0" /></label>
              <label>Preço de venda<input v-model.number="productForm.sale_price" type="number" step="0.01" min="0" required /></label>
            </div>
            <div class="form-row">
              <label>Estoque<input v-model.number="productForm.stock" type="number" min="0" required /></label>
              <label>Estoque mínimo<input v-model.number="productForm.minimum_stock" type="number" min="0" required /></label>
            </div>
            <label>Validade<input v-model="productForm.expiration_date" type="date" /></label>
            <div class="actions">
              <button class="primary" type="submit">Salvar produto</button>
              <button v-if="productForm.id" type="button" @click="resetProduct">Cancelar</button>
            </div>
          </form>

          <article class="panel">
            <h2>Produtos cadastrados</h2>
            <div v-for="p in products" :key="p.id" class="product">
              <div>
                <strong>{{ p.name }}</strong>
                <small>{{ p.category_name || 'Sem categoria' }} · {{ money(p.sale_price) }} · estoque {{ p.stock }}</small>
              </div>
              <div class="actions compact">
                <button @click="editProduct(p)">Editar</button>
                <button class="danger" @click="deleteProduct(p.id)">Excluir</button>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-if="tab === 'sales'">
        <header>
          <div>
            <span class="eyebrow">Movimentação</span>
            <h1>Registrar venda</h1>
            <p>A venda baixa o estoque e passa a fazer parte do histórico analisado pelo SAD.</p>
          </div>
        </header>

        <div class="grid-form">
          <form class="panel" @submit.prevent="registerSale">
            <h2>Nova venda</h2>
            <label>Produto
              <select v-model="saleForm.product" required>
                <option value="">Selecione</option>
                <option v-for="p in products.filter(x => x.active && x.stock > 0)" :key="p.id" :value="p.id">
                  {{ p.name }} · {{ money(p.sale_price) }} · {{ p.stock }} un.
                </option>
              </select>
            </label>
            <label>Quantidade<input v-model.number="saleForm.quantity" type="number" min="1" required /></label>
            <label>Desconto da venda<input v-model.number="saleForm.discount" type="number" min="0" step="0.01" /></label>
            <button class="primary" type="submit">Finalizar venda</button>
          </form>

          <article class="panel">
            <h2>Últimas vendas</h2>
            <div v-for="sale in sales.slice(0, 10)" :key="sale.id" class="product">
              <div>
                <strong>Venda #{{ sale.id }} · {{ money(sale.total) }}</strong>
                <small>{{ new Date(sale.created_at).toLocaleString('pt-BR') }}</small>
              </div>
            </div>
            <div v-if="!sales.length" class="empty">Nenhuma venda registrada.</div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>
