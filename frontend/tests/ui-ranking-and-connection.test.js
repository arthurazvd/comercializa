import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8')

test('gráficos têm formatos fixos e ranking fica limitado a dez produtos', () => {
  assert.match(app, /class="panel chart-panel top-products-chart"/)
  assert.match(app, /:rows="rankedRows" type="donut"/)
  assert.doesNotMatch(app, /productChartStyle/)
  assert.match(app, /:rows="trendRows" type="bar"/)
  assert.match(app, /:rows="categoryRows" type="donut"/)
  assert.doesNotMatch(app, /v-model="chartStyle"|v-model="categoryChartStyle"/)
  assert.match(css, /\.top-products-chart \.donut-layout \{[^}]*overflow: hidden;/)
  assert.match(css, /\.top-products-chart \.chart-legend \{[^}]*overflow-y: auto;/)
  assert.match(css, /\.top-products-chart \.top-product-list \{[^}]*overflow-y: auto;/)
})

test('consultas automáticas e gráficos não exibem toast genérico de conexão', () => {
  const section = app.slice(app.indexOf('async function refreshResources('), app.indexOf('async function loadAll('))
  assert.doesNotMatch(section, /alertUser\(/)
  const charts = app.slice(app.indexOf('async function refreshDashboardCharts('), app.indexOf('function refreshChartsAfterWrite('))
  assert.doesNotMatch(charts, /alertUser\(errorText/)
  assert.match(app, /chartError && !dashboardReport/)
  assert.doesNotMatch(app, /Não foi possível conectar à API/)
})

test('sem banner de verificação nem consultas extras de comprovante', () => {
  const api = readFileSync(new URL('../src/api.js', import.meta.url), 'utf8')
  assert.doesNotMatch(app, /writeConfirmationPending|pending-write-banner|Consultar dados/)
  assert.doesNotMatch(api, /continueConfirmation|findConfirmedPost|operations\/\$\{key\}\//)
  assert.match(app, /Versão \{\{ APP_VERSION \}\}/)
})
