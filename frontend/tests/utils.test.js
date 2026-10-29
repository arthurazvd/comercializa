import test from 'node:test'
import assert from 'node:assert/strict'
import { calculateCart, eligibleProducts, formatMoney, localDateISO, validCart } from '../src/utils.js'

const dateISO = '2026-10-29'
const products = [
  { id: 1, active: true, stock: 5, sale_price: '10.00', expiration_date: null },
  { id: 2, active: true, stock: 3, sale_price: '15.00', expiration_date: '2026-10-29' },
  { id: 3, active: true, stock: 5, sale_price: '20.00', expiration_date: '2026-10-28' },
  { id: 4, active: false, stock: 5, sale_price: '25.00', expiration_date: null },
  { id: 5, active: true, stock: 0, sale_price: '12.00', expiration_date: null },
]

test('carrinho suporta múltiplos itens com desconto', () => {
  assert.deepEqual(calculateCart([{ product: 1, quantity: 2 }, { product: 2, quantity: 3 }], products, 5), {
    subtotal: 65, total: 60,
  })
})
test('total nunca fica negativo', () => {
  assert.equal(calculateCart([{ product: 1, quantity: 1 }], products, 100).total, 0)
})
test('produto vence apenas após a data de validade', () => {
  assert.deepEqual(eligibleProducts(products, dateISO).map(p => p.id), [1, 2])
})
test('venda aceita itens distintos com quantidades disponíveis', () => {
  assert.equal(validCart([{ product: 1, quantity: 2 }, { product: 2, quantity: 1 }], products, 3, dateISO), true)
})
test('venda rejeita carrinho vazio, duplicado ou sem produto', () => {
  assert.equal(validCart([], products, 0, dateISO), false)
  assert.equal(validCart([{ product: 1, quantity: 1 }, { product: 1, quantity: 2 }], products, 0, dateISO), false)
  assert.equal(validCart([{ product: '', quantity: 1 }], products, 0, dateISO), false)
})
test('venda rejeita quantidade inválida e estoque insuficiente', () => {
  for (const qty of [0, -1, 1.5, 6]) {
    assert.equal(validCart([{ product: 1, quantity: qty }], products, 0, dateISO), false)
  }
})
test('venda rejeita produtos vencidos, inativos e sem estoque', () => {
  for (const id of [3, 4, 5]) {
    assert.equal(validCart([{ product: id, quantity: 1 }], products, 0, dateISO), false)
  }
})
test('venda rejeita descontos inválidos', () => {
  for (const discount of [-1, 11, NaN]) {
    assert.equal(validCart([{ product: 1, quantity: 1 }], products, discount, dateISO), false)
  }
})
test('datas locais têm formato ISO e não variam com locale', () => {
  assert.equal(localDateISO(new Date(2026, 9, 29)), '2026-10-29')
})
test('formata valor monetário em reais', () => {
  assert.match(formatMoney(10.5), /10,50/)
})
