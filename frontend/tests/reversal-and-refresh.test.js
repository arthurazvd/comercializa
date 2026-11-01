import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const file = name => readFileSync(new URL(`../${name}`, import.meta.url), 'utf8')

test('estorno tem confirmação, motivo, aviso financeiro e feedback', () => {
  const app = file('src/App.vue')
  for (const marker of ['openReversal(sale)', 'confirmReversal()', 'reversalReason',
      'sale-reversal', 'O sistema registra o valor devolvido', 'refunded_amount']) {
    assert.ok(app.includes(marker), marker)
  }
  assert.match(app, /postWithRecovery\(`sales\/\$\{saleId\}\/cancel\//)
})

test('gráficos não dependem da aba em que uma venda ocorreu', () => {
  const app = file('src/App.vue')
  const block = app.substring(app.indexOf('function refreshChartsAfterWrite()'), app.indexOf('function openReversal('))
  assert.match(block, /chartCache\.clear\(\)/)
  assert.match(block, /refreshDashboardCharts\(\{ silent: true, force: true \}\)/)
  assert.doesNotMatch(block, /if \(tab\.value === 'dashboard'\)/)
  assert.match(app, /chartErrorTimer = window\.setTimeout/)
})

test('API usa chave de idempotência sem endpoint de verificação', () => {
  const api = file('src/api.js')
  assert.doesNotMatch(api, /findConfirmedPost|operations\/\$\{key\}\//)
  assert.match(api, /__fresh: Date\.now\(\)/)
  assert.match(api, /pendingStorageName/)
  assert.match(api, /Idempotency-Key/)
})

test('campo selecionado não cria linha extra e mantém alinhamento em mobile', () => {
  const app = file('src/App.vue')
  const css = file('src/style.css')
  assert.doesNotMatch(app, /class="draft-selected"/)
  assert.match(app, /\{ 'is-selected': saleDraft\.product \}/)
  assert.match(css, /\.sale-draft-controls \{\s*display: grid;/)
  assert.match(css, /\.sale-search-box\.is-selected/)
})
