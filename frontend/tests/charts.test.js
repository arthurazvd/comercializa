import test from 'node:test'
import assert from 'node:assert/strict'
import { sortedSaleOptions, MOVEMENT_REASONS, movementNote, periodDates, aggregateDaily, productChartData, concentrationPercentage } from '../src/charts.js'
import { eligibleProducts, validCart } from '../src/utils.js'

test('campo vazio apresenta produtos alfabeticamente e ignora sem saldo vendável', () => {
  const products = [
    { id: 2, name: 'Zíper', active: true, stock: 5 },
    { id: 1, name: 'Água mineral', active: true, stock: 10 },
    { id: 3, name: 'Boné', active: true, stock: 2 },
    { id: 4, name: 'Caixa vencida', active: true, stock: 8, available_stock: 0 },
    { id: 5, name: 'Desativado', active: false, stock: 5 },
  ]
  assert.deepEqual(sortedSaleOptions(products).map(x => x.name), ['Água mineral', 'Boné', 'Zíper'])
  assert.deepEqual(sortedSaleOptions(products, 'BOn').map(x => x.name), ['Boné'])
  assert.deepEqual(sortedSaleOptions(products, 'nao existe'), [])
})

test('regras de venda impedem utilização de unidades vencidas em lote', () => {
  const products = [{ id: 1, name: 'Perecível', active: true, stock: 10, available_stock: 3, sale_price: 10, expiration_date: '2026-01-01' }]
  assert.equal(eligibleProducts(products, '2026-10-30').length, 1)
  assert.equal(validCart([{ product: 1, quantity: 3 }], products, 0, '2026-10-30'), true)
  assert.equal(validCart([{ product: 1, quantity: 4 }], products, 0, '2026-10-30'), false)
})

test('justificativas de entrada, saída e outro', () => {
  assert.ok(MOVEMENT_REASONS.find(x => x.value === 'avaria' && x.direction === 'out'))
  assert.equal(movementNote('recebimento'), 'Recebimento de mercadoria')
  assert.equal(movementNote('outro', 'Produto de mostruário'), 'Produto de mostruário')
  assert.equal(movementNote('outro', '  '), '')
  assert.equal(movementNote('inventario', 'Diferença de contagem'), 'Acerto de inventário — Diferença de contagem')
})

test('filtro de período e agrupamento por semana e mês', () => {
  assert.deepEqual(periodDates('7d', '2026-10-30'), { start: '2026-10-24', end: '2026-10-30' })
  assert.deepEqual(periodDates('30d', '2026-10-30'), { start: '2026-10-01', end: '2026-10-30' })
  assert.deepEqual(periodDates('12m', '2026-10-31'), { start: '2025-11-01', end: '2026-10-31' })
  const rows = [{ date: '2026-10-25', revenue: '10.50', quantity: 2 }, { date: '2026-10-26', revenue: '4.50', quantity: 1 }, { date: '2026-10-27', revenue: '6.00', quantity: 5 }]
  assert.deepEqual(aggregateDaily(rows, 'week'), [{ label: '2026-10-19', value: 10.5 }, { label: '2026-10-26', value: 10.5 }])
  assert.deepEqual(aggregateDaily(rows, 'month', 'quantity'), [{ label: '2026-10', value: 8 }])
})

test('ranking e concentração de categorias ignoram entradas vazias', () => {
  const rows = [{ name: 'Boné', quantity: 9, revenue: 30 }, { name: 'Pote', quantity: 2, revenue: 200 }]
  assert.deepEqual(productChartData(rows, 'revenue').map(x => x.label), ['Pote', 'Boné'])
  assert.equal(concentrationPercentage([{ revenue: 20 }, { revenue: 80 }]), 80)
  assert.equal(concentrationPercentage([]), 0)
})
