import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { APP_VERSION } from '../src/version.js'
const read = location => readFileSync(new URL(location, import.meta.url), 'utf8')
const app = read('../src/App.vue')
const css = read('../src/style.css')
const numeric = read('../src/components/NumericField.vue')

test('versão SemVer 1.1.0 corresponde ao package, aparece no footer e tira slogan', () => {
  assert.equal(APP_VERSION, '1.1.0')
  assert.equal(JSON.parse(read('../package.json')).version, APP_VERSION)
  assert.match(app, /Versão \{\{ APP_VERSION \}\}/)
  assert.doesNotMatch(app, /SEU NEGÓCIO EM MOVIMENTO/)
})

test('desktop mantém sidebar fixa no viewport sem rolagem própria; mobile conserva navegação inferior', () => {
  assert.match(css, /@media \(min-width: 851px\) \{[\s\S]*?\.sidebar \{[\s\S]*?position: sticky; top: 0;/)
  assert.match(css, /height: 100dvh; min-height: 0;/)
  assert.match(css, /overflow: hidden; overscroll-behavior: contain;/)
  assert.match(css, /\.sidebar nav \{ position: fixed; left: 0; right: 0; bottom: 0;/)
})

test('gráficos fixos: receita em barras, dez itens por unidades em rosca, categorias em rosca', () => {
  assert.match(app, /:rows="trendRows" type="bar"/)
  assert.match(app, /:rows="rankedRows" type="donut" :currency="false"/)
  assert.match(app, /:rows="categoryRows" type="donut"/)
  assert.match(app, /rankingDonutRows\([^)]*, 'quantity', 10\)/)
  assert.match(css, /\.dashboard-top \{ align-items: stretch; \}/)
  assert.match(css, /\.top-products-chart \.top-product-list \{[\s\S]*?max-height: 231px; overflow-y: auto;/)
  assert.doesNotMatch(app, /v-model="chartStyle"|v-model="categoryChartStyle"/)
})

test('toasts duram 1,5 segundo, com mesma duração para erros e sucessos', () => {
  assert.match(read('../src/toast.js'), /duration = 1500/)
  assert.match(css, /animation: toastProgress 1\.5s linear forwards;/)
})

test('campos numéricos têm botões acessíveis, com limites de quantidade no celular', () => {
  assert.match(numeric, /aria-label="`Diminuir \$\{label\}`"/)
  assert.match(numeric, /aria-label="`Aumentar \$\{label\}`"/)
  assert.match(numeric, /Math\.min\(upper\.value, Math\.max\(lower\.value,/)
  assert.match(css, /@media \(max-width: 850px\) \{[\s\S]*?\.numeric-control \{/)
  assert.match(app, /<NumericField v-model="saleDraft\.quantity"/)
  assert.match(app, /<NumericField v-model="item\.quantity"/)
  assert.match(app, /<NumericField v-model="stockDelta"/)
})

test('rolagem recebe cores personalizadas nos dois temas', () => {
  assert.match(css, /--scroll-thumb: #a5bbcc/)
  assert.match(css, /--scroll-thumb: #49677a/)
  assert.match(css, /\*::-webkit-scrollbar-thumb/)
})
