import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
const read = path => readFileSync(new URL(path, import.meta.url), 'utf8')
const app = read('../src/App.vue')
const css = read('../src/style.css')

test('catalog isolates image, product name, prices and actions instead of squeezing text', () => {
  assert.match(app, /class="catalog-actions inline-actions"/)
  assert.match(css, /\.catalog-item\s*\{\s*display: grid; grid-template-columns: 54px minmax\(0, 1fr\) auto/)
  assert.match(css, /\.catalog-item \.product-info strong\s*\{[^}]*word-break: normal/)
})
test('inventory displays authenticated thumbnails and opens a product preview', () => {
  assert.match(app, /class="stock-product-link"[^>]*@click="openInventoryProduct\(p\)"/)
  assert.match(app, /modal === 'stock-product'/)
  assert.match(app, /products\/\$\{product.id\}\/lots\//)
  assert.match(app, /size="inventory"/)
  assert.match(css, /\.stock-detail-main\s*\{/)
})
test('purchases save cost per lot and optionally change current reference and selling price', () => {
  assert.match(app, /const isPurchaseReceipt = computed/)
  assert.match(app, /unit_cost: Number\(receiptUnitCost.value\)/)
  assert.match(app, /update_reference_cost: receiptUpdateReference.value/)
  assert.match(app, /new_sale_price: Number\(receiptNewSalePrice.value\)/)
  assert.match(app, /const movementCostValid = computed/)
  assert.match(app, /stockItemOverview.get\(p.id\)\?\.stock_value/)
})
