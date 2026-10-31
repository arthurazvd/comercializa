import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
const read = path => readFileSync(join(import.meta.dirname, '..', path), 'utf8')

test('operação idempotente protege cadastros, vendas e ajustes', () => {
  const api = read('src/api.js')
  const app = read('src/App.vue')
  assert.match(api, /Idempotency-Key/)
  assert.match(api, /pendingPosts/)
  assert.match(api, /isTransientFailure/)
  for (const path of ["products/", "categories/", "sales/", "stock-movements/"]) {
    assert.ok(app.includes(`postWithRecovery('${path}'`), path)
  }
  assert.match(app, /writeErrorText/)
})

test('primeiro acesso é seletivo, gráficos podem atualizar sem recarregar tudo', () => {
  const app = read('src/App.vue')
  assert.match(app, /refreshResources\(\['products', 'categories', 'dashboard'\]/)
  assert.match(app, /function refreshVisibleData\(/)
  assert.match(app, /chartCache\.set\(/)
  assert.match(app, /chartUpdatedAt/)
  assert.match(app, /visibilitychange/)
  assert.match(app, /chartAbortController\?\.abort\(\)/)
})

test('logo da autenticação é horizontal e navegação mobile usa barra inferior', () => {
  const app = read('src/App.vue')
  const css = read('src/style.css')
  assert.match(app, /class="auth-logo"/)
  assert.match(app, /theme === 'dark' \? BRAND_ASSETS.horizontalOnDark : BRAND_ASSETS.horizontalOnLight/)
  assert.match(css, /\.sidebar nav \{ position: fixed; left: 0; right: 0; bottom: 0;/)
  assert.match(css, /safe-area-inset-bottom/)
  assert.match(css, /\.modal-backdrop \{ z-index: 120; \}/)
})
