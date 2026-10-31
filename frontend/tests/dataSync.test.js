import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { createLatestLoader, upsertById, removeById } from '../src/dataSync.js'

const app = readFileSync(join(import.meta.dirname, '../src/App.vue'), 'utf8')
const deferred = () => {
  let resolve, reject
  const promise = new Promise((res, rej) => { resolve = res; reject = rej })
  return { promise, resolve, reject }
}

test('cadastrar / atualizar / excluir altera catálogo sem duplicar registros', () => {
  const original = [{ id: 1, name: 'Antigo' }]
  const added = upsertById(original, { id: 2, name: 'Boné' })
  assert.deepEqual(added.map(p => p.name), ['Boné', 'Antigo'])
  const changed = upsertById(added, { id: 2, name: 'Boné editado' })
  assert.equal(changed.length, 2)
  assert.equal(changed[0].name, 'Boné editado')
  assert.deepEqual(removeById(changed, 2), original)
})

test('GET anterior a um cadastro não sobrescreve cadastro confirmado', async () => {
  const slow = deferred()
  const displayed = []
  const loader = createLatestLoader(() => slow.promise, (_name, data) => displayed.push(data))
  const pending = loader.load('products')
  loader.invalidate('products') // produto salvo com POST
  slow.resolve([{ id: 1, name: 'Lista antiga' }])
  await pending
  assert.deepEqual(displayed, [])
})

test('apenas consulta mais recente pode atualizar a mesma lista', async () => {
  const first = deferred(), second = deferred()
  let order = 0
  const displayed = []
  const loader = createLatestLoader(() => (++order === 1 ? first.promise : second.promise), (_name, data) => displayed.push(data))
  const oldQuery = loader.load('products')
  const freshQuery = loader.load('products')
  second.resolve('nova')
  await freshQuery
  first.resolve('antiga')
  await oldQuery
  assert.deepEqual(displayed, ['nova'])
})

test('falha em uma consulta não impede as demais consultas independentes', async () => {
  const displayed = {}
  const loader = createLatestLoader(name => name === 'dashboard' ? Promise.reject(new Error('offline')) : Promise.resolve([name]), (name, data) => { displayed[name] = data })
  const outcome = await Promise.allSettled(['products', 'dashboard', 'categories'].map(name => loader.load(name)))
  assert.equal(outcome.filter(r => r.status === 'fulfilled').length, 2)
  assert.deepEqual(Object.keys(displayed).sort(), ['categories', 'products'])
})

test('cadastro, exclusão e venda não dependem do carregamento global para sucesso', () => {
  for (const method of ['saveProduct', 'deleteProduct', 'addCategory', 'registerSale', 'adjustStock']) {
    const block = app.split(`async function ${method}(`)[1].split('\nasync function ')[0].split('\nfunction ')[0]
    assert.ok(!block.includes('await loadAll()'), `${method} não pode esperar seis consultas`)
  }
  assert.match(app, /products\.value = upsertById\(products\.value, response\.data\)/)
  assert.match(app, /products\.value = removeById\(products\.value, product\.id\)/)
})
