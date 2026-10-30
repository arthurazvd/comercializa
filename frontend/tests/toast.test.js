import test from 'node:test'
import assert from 'node:assert/strict'
import { createToastController } from '../src/toast.js'

test('toast desaparece após 2 segundos', () => {
  const updates = []
  const jobs = new Map()
  let id = 0
  const scheduler = { setTimeout: callback => { jobs.set(++id, callback); return id }, clearTimeout: key => jobs.delete(key) }
  const toast = createToastController(value => updates.push(value), 2000, scheduler)
  toast.show('Venda salva')
  assert.deepEqual(updates.at(-1), { text: 'Venda salva', type: 'success' })
  assert.equal(jobs.size, 1)
  jobs.values().next().value()
  assert.equal(updates.at(-1), null)
})

test('novo toast reinicia cronômetro e erros são tratados igualmente', () => {
  const updates = []
  const jobs = new Map()
  let id = 0
  const scheduler = { setTimeout: cb => { jobs.set(++id, cb); return id }, clearTimeout: key => jobs.delete(key) }
  const toast = createToastController(value => updates.push(value), 2000, scheduler)
  toast.show('Cadastrado')
  toast.show('Estoque insuficiente', 'error')
  assert.equal(jobs.size, 1)
  assert.deepEqual(updates.at(-1), { text: 'Estoque insuficiente', type: 'error' })
  toast.dismiss()
  assert.equal(jobs.size, 0)
  assert.equal(updates.at(-1), null)
})
