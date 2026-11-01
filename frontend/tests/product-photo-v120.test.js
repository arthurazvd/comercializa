import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { productPhotoFilename, checkOriginalPhoto, PRODUCT_IMAGE_MAX_BYTES } from '../src/imageProcessing.js'
import { APP_VERSION } from '../src/version.js'
import { createToastController } from '../src/toast.js'
const read = path => readFileSync(new URL(path, import.meta.url), 'utf8')
const app = read('../src/App.vue')
const css = read('../src/style.css')
const backend = read('../../backend/core/views.py')

// Verificações unitárias de campos e contratos de integração; NÃO substituem teste E2E.
test('versão 1.2.0 é a mesma do manifesto', () => {
  assert.equal(APP_VERSION, '1.2.0')
  assert.equal(JSON.parse(read('../package.json')).version, APP_VERSION)
})
test('nomes de arquivo seguem SKU e terminam em JPEG, sem diretórios', () => {
  assert.equal(productPhotoFilename('A/B 1:2'), 'A-B-1-2.jpg')
  assert.equal(productPhotoFilename('CÓDIGO 003'), 'CODIGO-003.jpg')
  assert.equal(productPhotoFilename(''), 'produto.jpg')
})
test('entrada rejeita não-imagem, 20MB e arquivo ausente', () => {
  assert.throws(() => checkOriginalPhoto(null), /Selecione/)
  assert.throws(() => checkOriginalPhoto({ type: 'text/plain', size: 100 }), /imagem/)
  assert.throws(() => checkOriginalPhoto({ type: 'image/png', size: 21 * 1024 * 1024 }), /20 MB/)
  assert.doesNotThrow(() => checkOriginalPhoto({ type: 'image/jpeg', size: 15 * 1024 }))
  assert.equal(PRODUCT_IMAGE_MAX_BYTES, 102400)
})
test('foto é convertida com Canvas para JPEG, limitada a 100KB e mantém proporções', () => {
  const src = read('../src/imageProcessing.js')
  assert.match(src, /canvas\.toBlob\(/)
  assert.match(src, /'image\/jpeg'/)
  assert.match(src, /Math\.min\(side \/ image\.naturalWidth, side \/ image\.naturalHeight\)/)
  assert.match(src, /blob\.size > 0 && blob\.size <= PRODUCT_IMAGE_MAX_BYTES/)
})
test('cadastro e edição oferecem captura da câmera, galeria, remoção e prévia', () => {
  assert.match(app, /ref="photoGalleryInput"[^>]*accept="image\/\*"/)
  assert.match(app, /ref="photoCameraInput"[^>]*capture="environment"/)
  assert.match(app, /Prévia da nova fotografia do produto/)
  assert.match(app, /function discardPhoto\(/)
  assert.match(app, /function editProduct\(product\)/)
  assert.match(css, /\.product-photo-editor/)
})
test('salva produto antes da foto e guarda id quando upload falha, para não duplicar', () => {
  assert.match(app, /saved = response\.data[\s\S]*?productForm\.value\.id = saved\.id/)
  assert.match(app, /api\.put\(`products\/\$\{saved\.id\}\/image\/`, form\)/)
  assert.match(app, /Produto salvo, mas a foto não foi atualizada/)
  assert.match(app, /api\.delete\(`products\/\$\{saved\.id\}\/image\/`\)/)
})
test('o backend isola fotos dos JSONs de listagem, exige autenticação e usa banco persistente', () => {
  const models = read('../../backend/core/models.py')
  const serializer = read('../../backend/core/serializers.py')
  assert.match(models, /class ProductImage\(models\.Model\)/)
  assert.match(models, /data = models\.BinaryField\(\)/)
  assert.match(serializer, /"has_image", "image_updated_at"/)
  assert.match(backend, /methods=\['get', 'put', 'delete'\]/)
  assert.match(backend, /ProductImage\.objects\.update_or_create/)
  assert.match(backend, /photo\.size > 102400/)
})
test('carregamento de foto usa blob autenticado e carrega apenas quando visível', () => {
  const thumbnail = read('../src/components/ProductThumbnail.vue')
  assert.match(thumbnail, /responseType: 'blob'/)
  assert.match(thumbnail, /IntersectionObserver/)
  assert.match(thumbnail, /URL\.revokeObjectURL/)
})
test('o toast é encerrado pela animação e pelo timer, reinicia com notificações novas', () => {
  assert.match(app, /@animationend="closeToastAtProgressEnd\(toast\.id\)"/)
  assert.match(app, /:key="toast\.id"/)
  assert.match(css, /animation: toastProgress 1\.5s linear forwards/)
  let current, id = 0
  const tasks = new Map()
  const controller = createToastController(v => { current = v }, 1500,
    { setTimeout(fn) { tasks.set(++id, fn); return id }, clearTimeout(k) { tasks.delete(k) } })
  controller.show('Primeira'); const first = current.id
  controller.show('Segunda'); assert.notEqual(current.id, first)
  assert.equal(tasks.size, 1)
  tasks.values().next().value()
  assert.equal(current, null)
})
