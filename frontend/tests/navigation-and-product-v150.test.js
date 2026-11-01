import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { TAB_PATHS, FINANCE_PATH, pathForTab, tabFromPath, normalizePath, isKnownPagePath, isFinancePath } from '../src/navigation.js'
const read = filename => readFileSync(new URL(filename, import.meta.url), 'utf8')
const app = read('../src/App.vue')
const css = read('../src/style.css')
const models = read('../../backend/core/models.py')
const serializers = read('../../backend/core/serializers.py')
const api = read('../src/api.js')

test('cada tela principal tem endereço próprio e reload preserva a seção', () => {
  const expected = { dashboard: '/visao-geral', sales: '/vendas', products: '/produtos', inventory: '/estoque', movements: '/movimentacoes' }
  assert.deepEqual(TAB_PATHS, expected)
  for (const [name, path] of Object.entries(expected)) {
    assert.equal(pathForTab(name), path)
    assert.equal(tabFromPath(path), name)
    assert.equal(tabFromPath(path + '/'), name)
    assert.ok(isKnownPagePath(path))
  }
  assert.equal(normalizePath('/estoque/?foo=1'), '/estoque')
  assert.equal(tabFromPath('/inexistente'), 'dashboard')
  assert.equal(FINANCE_PATH, '/financeiro')
  assert.ok(isFinancePath('/financeiro/'))
  assert.match(app, /const tab = ref\(tabFromPath\(window\.location\.pathname\)\)/)
  assert.match(app, /window\.history\.pushState/)
  assert.match(app, /addEventListener\('popstate', onHistoryNavigation\)/)
  assert.match(app, /PAGE_RESOURCES\[tab\.value\]/)
  assert.match(app, /inventory: \['stockOverview', 'products'\]/)
  assert.match(app, /removeEventListener\('popstate', onHistoryNavigation\)/)
  assert.match(read('../public/_redirects'), /\/\* \/index\.html 200/)
})

test('cadastro libera botão mesmo que a interface ou a foto falhe após 201', () => {
  const code = app.slice(app.indexOf('async function saveProduct()'), app.indexOf('async function toggleProduct('))
  assert.match(code, /confirmed = true/)
  assert.match(code, /finally \{[\s\S]*?busy\.value = false/)
  assert.match(code, /productForm\.value\.id = saved\.id/)
  assert.match(code, /api\.put\(`products\/\$\{saved\.id\}\/image\/`, form, \{ timeout: 30000 \}\)/)
  assert.match(code, /postWithRecovery\('products\/', payload, \{ timeout: 40000 \}\)/)
  assert.match(api, /export async function postWithRecovery\(url, payload, \{ timeout = 95000 \} = \{\}\)/)
  assert.match(code, /Se[m]? resposta da API/)
  assert.doesNotMatch(code, /api\.get\('operations\//)
})

test('descrição é opcional, persiste no modelo e aparece no formulário e nos detalhes', () => {
  assert.match(models, /description = models\.TextField\(blank=True, default=""\)/)
  assert.match(serializers, /description = serializers\.CharField\(required=False, allow_blank=True, max_length=2000\)/)
  assert.match(serializers, /"id", "name", "description", "category"/)
  assert.match(app, /v-model="productForm\.description" maxlength="2000"/)
  assert.match(app, /stockDetailProduct\.description/)
  assert.match(app, /imageViewerProduct\.description/)
  assert.match(app, /p\.description/)
})

test('busca tem somente foco externo e foto permite zoom sem modificar JPEG', () => {
  assert.match(css, /label\.search-input input\[type="search"\]:focus-visible/)
  assert.match(css, /outline: 0 !important; outline-offset: 0; box-shadow: none !important/)
  assert.match(app, /openProductImage\(stockDetailProduct\)/)
  assert.match(app, /openProductImage\(p\)/)
  assert.match(app, /imageViewerMode === 'crop'/)
  assert.match(css, /product-image-canvas\.show-entire[\s\S]*?object-fit: contain/)
  assert.match(css, /photo-view-button[^\n]*?product-thumbnail img \{ transform: scale\(1\.07\)/)
})
