import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const readJSON = file => JSON.parse(readFileSync(new URL(file, import.meta.url), 'utf8'))

test('npm lock has a satisfiable es-object-atoms requirement', () => {
  const lock = readJSON('../package-lock.json')
  const manifest = readJSON('../package.json')
  const required = lock.packages['node_modules/get-intrinsic'].dependencies['es-object-atoms']
  const installed = lock.packages['node_modules/es-object-atoms'].version
  assert.equal(required, '^1.1.1')
  assert.equal(installed, '1.1.2')
  assert.equal(lock.packages[''].version, manifest.version)
  assert.equal(lock.version, manifest.version)
})
