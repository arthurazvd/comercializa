import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { createToastController } from '../src/toast.js'
import { APP_VERSION } from '../src/version.js'

const get = file => readFileSync(new URL(file, import.meta.url), 'utf8')
const app = get('../src/App.vue')
const css = get('../src/style.css')

// Contract tests ensure that direct catalog actions are connected to the existing
// authenticated image endpoint; a real Cloudflare + Render smoke test is still necessary.
test('visible version matches SemVer manifest', () => {
  assert.equal(APP_VERSION, '1.2.2')
  assert.equal(JSON.parse(get('../package.json')).version, APP_VERSION)
  assert.match(app, /Versão \{\{ APP_VERSION \}\}/)
})
test('each product offers a direct photo control inside the catalog', () => {
  assert.match(app, /class="catalog-photo-action"/)
  assert.match(app, /@click="openCatalogPhoto\(p\)"/)
  assert.match(app, /Adicionar foto/)
  assert.match(app, /modal === 'product-photo'/)
  assert.match(app, /modalTitles = \{[^\n]*'product-photo': 'Foto do produto'/)
})
test('catalog modal opens camera and gallery and normalizes JPEG', () => {
  assert.match(app, /ref="catalogGalleryInput"[^>]+accept="image\/\*"/)
  assert.match(app, /ref="catalogCameraInput"[^>]+capture="environment"/)
  assert.match(app, /normalizeProductPhoto\(file, catalogPhotoProduct\.value\.sku \|\| catalogPhotoProduct\.value\.id\)/)
  assert.match(app, /catalogPhotoPreview/)
  assert.match(css, /\.catalog-photo-modal/)
})
test('catalog photo actions send authenticated request to existing API and update thumbnail', () => {
  assert.match(app, /api\.put\(`products\/\$\{productId\}\/image\/`, data\)/)
  assert.match(app, /api\.delete\(`products\/\$\{productId\}\/image\/`\)/)
  assert.match(app, /products\.value = upsertById\(products\.value, \{ \.\.\.catalogPhotoProduct\.value, \.\.\.response\.data \}\)/)
  assert.match(app, /invalidateResource\('products'\)/)
  assert.match(app, /modal\.value = ''\s+alertUser\('Foto/)
})
test('notification has a visual timeout independent of JS and auto dismisses when time expires', async () => {
  assert.match(app, /@animationend="closeToastAtProgressEnd\(toast\.id\)"/)
  assert.match(css, /\.toast-notice \{ animation: toastVisualExpiry 1\.5s linear both; \}/)
  assert.match(css, /100% \{ opacity: 0; visibility: hidden; \}/)
  let latest = null
  const controller = createToastController(message => { latest = message }, 25)
  controller.show('Produto cadastrado com sucesso.')
  assert.equal(latest?.text, 'Produto cadastrado com sucesso.')
  await new Promise(resolve => setTimeout(resolve, 75))
  assert.equal(latest, null)
  controller.dispose()
})
test('Cloudflare deployment always requests fresh index to avoid stale V1.1 bundle', () => {
  assert.match(get('../public/_headers'), /Cache-Control: no-cache, no-store, must-revalidate/)
})
