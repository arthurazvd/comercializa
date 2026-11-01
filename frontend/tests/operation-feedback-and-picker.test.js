import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { actionableWriteMessage } from '../src/operationFeedback.js'

const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8')

test('erros genéricos de rede, 5xx e erros de código não geram notificação falsa de cadastro', () => {
  assert.equal(actionableWriteMessage(Object.assign(new Error('ERR_NETWORK'), { code: 'ERR_NETWORK' })), '')
  assert.equal(actionableWriteMessage(Object.assign(new Error('timeout'), { code: 'ECONNABORTED' })), '')
  assert.equal(actionableWriteMessage(new TypeError('Cannot read properties of undefined')), '')
  assert.equal(actionableWriteMessage({ response: { status: 500, data: { detail: 'Erro interno' } } }), '')
  assert.equal(actionableWriteMessage({ response: { status: 401, data: { detail: 'Sem login' } } }), '')
  assert.equal(actionableWriteMessage({ response: { status: 400, data: null } }), '')
})

test('erros HTTP explícitos de validação e permissão continuam legíveis', () => {
  assert.equal(actionableWriteMessage({ response: { status: 400, data: { name: ['Este campo é obrigatório.'] } } }), 'name: Este campo é obrigatório.')
  assert.equal(actionableWriteMessage({ response: { status: 403, data: { detail: 'Sem permissão.' } } }), 'Sem permissão.')
  assert.equal(actionableWriteMessage({ response: { status: 409, data: { detail: 'Chave já utilizada.' } } }), 'Chave já utilizada.')
})

test('operação sem resposta não gera o toast genérico e não limpa o formulário', () => {
  const handler = app.slice(app.indexOf('function notifyWriteFailure('), app.indexOf('function notifyReadFailure('))
  assert.doesNotMatch(handler, /errorText\(/)
  assert.doesNotMatch(handler, /writeErrorText/)
  assert.match(handler, /actionableWriteMessage\(error\)/)
  assert.match(handler, /refreshVisibleData\(\)/)
  assert.doesNotMatch(handler, /resetProduct\(/)
})

test('busca do PDV permanece dentro do fluxo, sem lista flutuante sobre o carrinho', () => {
  const start = app.indexOf('<div class="sale-draft">')
  const end = app.indexOf('<div class="cart-heading">', start)
  const field = app.slice(start, end)
  assert.match(field, /class="sale-draft-controls"/)
  assert.match(field, /class="sale-results"/)
  assert.match(field, /Limpar produto selecionado/)
  assert.match(css, /\.sale-draft \.sale-results \{[\s\S]*?position: static;/)
  assert.match(css, /\.sale-draft \.sale-search-box input:focus-visible \{ outline: none;/)
  assert.match(css, /@container \(max-width: 530px\)/)
})
