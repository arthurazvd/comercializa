import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const source = readFileSync(new URL('../src/api.js', import.meta.url), 'utf8')
  .replace("import axios from 'axios'", 'const axios = globalThis.__comercializaAxiosMock')
  .replace('import.meta.env.VITE_API_URL', "''")

async function setup({ post, get }) {
  const entries = new Map()
  globalThis.window = {
    sessionStorage: {
      getItem: key => entries.get(key) ?? null,
      setItem: (key, value) => entries.set(key, value),
      removeItem: key => entries.delete(key),
    },
  }
  globalThis.__comercializaAxiosMock = {
    isCancel: error => error?.code === 'ERR_CANCELED',
    isAxiosError: error => error?.isAxiosError === true,
    create: () => ({
      post, get,
      interceptors: { request: { use() {} }, response: { use() {} } },
    }),
  }
  const module = await import(`data:text/javascript;charset=utf-8,${encodeURIComponent(source)}#${Math.random()}`)
  return { module, entries }
}

function timeout() {
  return Object.assign(new Error('timeout'), { isAxiosError: true, code: 'ECONNABORTED' })
}

test('HTTP 201 é confirmação definitiva: não mostra falha nem repete POST', async () => {
  let sent = 0
  const { module: app, entries } = await setup({
    post: async () => { sent += 1; return { status: 201, data: { id: 12, name: 'Brinquedos' } } },
    get: async () => { throw new Error('GET não esperado') },
  })
  const result = await app.postWithRecovery('categories/', { name: 'Brinquedos' })
  assert.equal(result.status, 201)
  assert.equal(result.data.name, 'Brinquedos')
  assert.equal(sent, 1)
  assert.equal([...entries.keys()].filter(key => key.startsWith('comercializa_op_')).length, 0)
  assert.equal(app.isTransientFailure(new TypeError('Erro de interface depois do 201')), false)
  assert.equal(app.writeErrorText(new TypeError('Erro de interface'), () => 'Erro na interface'), 'Erro na interface')
})

test('timeout do POST com registro confirmado recupera sucesso sem duplicação', async () => {
  let sent = 0
  let key
  const { module: app } = await setup({
    post: async (_url, _data, config) => {
      sent += 1
      key = config.headers['Idempotency-Key']
      throw timeout()
    },
    get: async path => {
      assert.equal(path, `operations/${key}/`)
      return { data: { confirmed: true, status: 201, path: '/api/categories/', data: { id: 44, name: 'Carrinhos' } } }
    },
  })
  const result = await app.postWithRecovery('categories/', { name: 'Carrinhos' })
  assert.equal(result.status, 201)
  assert.equal(result.data.id, 44)
  assert.equal(sent, 1)
})

test('desconexão real conserva chave e não exibe o aviso falso de operação não confirmada', async () => {
  const keys = []
  const { module: app, entries } = await setup({
    post: async (_url, _data, config) => {
      keys.push(config.headers['Idempotency-Key'])
      throw timeout()
    },
    get: async () => { throw Object.assign(new Error('not found'), { response: { status: 404 }, isAxiosError: true }) },
  })
  await assert.rejects(() => app.postWithRecovery('categories/', { name: 'Novidades' }), e => {
    assert.equal(app.isWritePending(e), true)
    assert.equal(app.writeErrorText(e, () => 'Falha real'), '')
    return true
  })
  assert.equal(keys.length, 2)
  assert.equal(keys[0], keys[1])
  assert.equal([...entries.keys()].filter(key => key.startsWith('comercializa_op_')).length, 1)
})

test('erro na atualização da tela após HTTP 201 não produz toast de falha de cadastro', () => {
  const appSource = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
  const start = appSource.indexOf('function applyConfirmedWrite(')
  const end = appSource.indexOf('function errorText(', start)
  const notifications = []
  let refreshes = 0
  const createHandler = new Function('console', 'alertUser', 'refreshVisibleData',
    `${appSource.slice(start, end)}; return applyConfirmedWrite`)
  const handle = createHandler({ error() {} }, (text, type = 'success') => notifications.push({ text, type }), () => { refreshes += 1 })
  handle(() => { throw new TypeError('Falha no componente após HTTP 201') }, { status: 201, data: { id: 1 } })
  assert.equal(notifications.length, 1)
  assert.equal(notifications[0].type, 'success')
  assert.equal(refreshes, 1)
})
