import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
const source = file => readFileSync(join(import.meta.dirname, '..', file), 'utf8')

test('API identifica origem Render e anexa token', () => {
  assert.match(source('src/api.js'), /VITE_API_URL/)
  assert.match(source('src/api.js'), /Token \${token}/)
  assert.match(source('src/api.js'), /sessionStorage/)
})
test('tela de login impede acesso sem autenticação', () => {
  assert.match(source('src/App.vue'), /authRequired && !authenticated/)
  assert.match(source('src/App.vue'), /auth\/login\//)
  assert.match(source('src/App.vue'), /auth\/status\//)
  assert.match(source('src/App.vue'), /signOut/)
})
