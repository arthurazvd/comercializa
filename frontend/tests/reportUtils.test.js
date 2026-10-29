import test from 'node:test'
import assert from 'node:assert/strict'
import { defaultReportFilters, queryReport, inventoryStatus, matchProductSearch, filteredInventory } from '../src/reportUtils.js'

test('filtros financeiros default usam início do mês local', () => {
  assert.deepEqual(defaultReportFilters(new Date(2026, 9, 29)), {
    start: '2026-10-01', end: '2026-10-29', category: '', product: '',
  })
})
test('URL codifica período e filtros opcionais', () => {
  assert.equal(queryReport({ start: '2026-01-01', end: '2026-01-31', category: 2, product: 3 }),
    'start=2026-01-01&end=2026-01-31&category=2&product=3')
})
test('consulta de produtos ignora caixa e inclui SKU', () => {
  assert.equal(matchProductSearch({ name: 'Chapéu de palha', sku: 'VEST-002' }, 'chapÉu'), true)
  assert.equal(matchProductSearch({ name: 'Chapéu de palha', sku: 'VEST-002' }, 'vest-002'), true)
  assert.equal(matchProductSearch({ name: 'Chapéu de palha' }, 'carregador'), false)
})
test('classificação tem prioridade para vencido e validade próxima', () => {
  const base = { active: true, stock: 2, minimum_stock: 5 }
  assert.equal(inventoryStatus({ ...base, expiration_date: '2026-10-28' }, '2026-10-29'), 'vencido')
  assert.equal(inventoryStatus({ ...base, expiration_date: '2026-11-04' }, '2026-10-29'), 'a_vencer')
  assert.equal(inventoryStatus(base, '2026-10-29'), 'critico')
  assert.equal(inventoryStatus({ ...base, active: false }, '2026-10-29'), 'inativo')
})
test('estoque crítico inclui produtos vencidos com saldo baixo', () => {
  const sample = [{ id: 1, name: 'Pote', category: 1, active: true, stock: 1, minimum_stock: 3, expiration_date: '2020-01-01' },
    { id: 2, name: 'Boné', category: 2, active: true, stock: 12, minimum_stock: 3 }]
  assert.deepEqual(filteredInventory(sample, '', 'critico').map(p => p.id), [1])
  assert.deepEqual(filteredInventory(sample, 'bon', 'all').map(p => p.id), [2])
})
