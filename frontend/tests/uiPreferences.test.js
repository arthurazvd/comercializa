import test from 'node:test'
import assert from 'node:assert/strict'
import { readTheme, saveTheme } from '../src/uiPreferences.js'

test('tema padrão é claro e respeita escolha escura', () => {
  assert.equal(readTheme(() => ({ getItem: () => 'dark' })), 'dark')
  assert.equal(readTheme(() => ({ getItem: () => 'invalido' })), 'light')
})
test('tema persiste no navegador sem aceitar valores inválidos', () => {
  const store = new Map()
  const storage = { getItem: k => store.get(k), setItem: (k, v) => store.set(k, v) }
  assert.equal(saveTheme('dark', () => storage), true)
  assert.equal(readTheme(() => storage), 'dark')
  assert.equal(saveTheme('other', () => storage), false)
})
test('tema funciona mesmo se armazenamento estiver bloqueado', () => {
  const fail = () => { throw Error('Bloqueado') }
  assert.equal(readTheme(fail), 'light')
  assert.equal(saveTheme('dark', fail), false)
})
