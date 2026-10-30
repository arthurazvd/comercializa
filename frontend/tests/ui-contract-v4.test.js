import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const source = f => readFileSync(join(root, f), 'utf8')

test('a entrada de venda é fixa antes dos itens da venda e abre catálogo ao focar', () => {
  const app = source('src/App.vue')
  const panel = app.split('class="panel sale-panel"')[1].split('</form>')[0]
  assert.ok(panel.indexOf('class="sale-draft"') < panel.indexOf('class="cart-heading"'))
  assert.ok(panel.indexOf('class="sale-draft"') < panel.indexOf('v-for="(item, index) in saleForm.items"'))
  assert.match(panel, /@focus="showSaleOptions"/)
  assert.match(panel, /role="listbox"/)
  assert.match(panel, /v-for="p in saleChoices"/)
})

test('avisos têm fechamento automático e acessibilidade', () => {
  const app = source('src/App.vue')
  assert.match(app, /createToastController/)
  assert.match(app, /toast\.type === 'error' \? 'alert' : 'status'/)
  assert.match(app, /toastController\.dispose\(\)/)
  const css = source('src/style.css')
  assert.match(css, /\.toast-notice \{/)
  assert.match(css, /toastProgress 2s/)
})

test('recebimento perecível solicita data, gráficos têm controles e logo é compacta', () => {
  const app = source('src/App.vue')
  assert.match(app, /Nova validade do lote/)
  assert.match(app, /v-if="showingReceiptExpiry"/)
  assert.match(app, /v-model="stockReason"/)
  assert.match(app, /v-model="chartPeriod"/)
  assert.match(app, /v-model="chartGrouping"/)
  assert.match(app, /v-model="chartStyle"/)
  assert.match(app, /v-model="productChartStyle"/)
  assert.match(app, /v-model="categoryChartStyle"/)
  assert.match(source('src/style.css'), /\.brand-logo-vertical \{ width: 110px; height: 151px;/)
})
