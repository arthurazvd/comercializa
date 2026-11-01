import test from 'node:test'
import assert from 'node:assert/strict'
import { addOrIncrementCartItem } from '../src/cart.js'
import { validCart } from '../src/utils.js'

const product = { id: 7, name: 'Boné', stock: 50, available_stock: 3, active: true, sale_price: 25 }

test('incluir o mesmo produto soma a quantidade em uma linha única', () => {
  const first = addOrIncrementCartItem([], product, 1, 11)
  assert.equal(first.ok, true)
  assert.equal(first.merged, false)
  const second = addOrIncrementCartItem(first.items, product, 1, 12)
  assert.equal(second.ok, true)
  assert.equal(second.merged, true)
  assert.deepEqual(second.items, [{ product: 7, quantity: 2, key: 11 }])
  assert.equal(validCart(second.items, [product]), true)
})

test('não ultrapassa estoque disponível, mesmo que o saldo físico seja maior', () => {
  const original = [{ product: 7, quantity: 2, key: 11 }]
  const rejected = addOrIncrementCartItem(original, product, 2, 12)
  assert.equal(rejected.ok, false)
  assert.strictEqual(rejected.items, original)
  assert.equal(original[0].quantity, 2)
  assert.match(rejected.reason, /Estoque insuficiente/)
})

test('diferentes produtos mantêm linhas separadas e quantidades inteiras', () => {
  const product2 = { id: 8, active: true, available_stock: 6 }
  const result = addOrIncrementCartItem([{ product: 7, quantity: 1, key: 1 }], product2, 2, 2)
  assert.deepEqual(result.items.map(row => row.product), [7, 8])
  assert.equal(addOrIncrementCartItem(result.items, product2, 0, 3).ok, false)
  assert.equal(addOrIncrementCartItem(result.items, product2, 1.5, 3).ok, false)
  assert.equal(addOrIncrementCartItem(result.items, { ...product, active: false }, 1, 3).ok, false)
})
