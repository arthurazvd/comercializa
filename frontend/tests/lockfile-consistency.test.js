import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const manifest = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'))
const lock = JSON.parse(readFileSync(new URL('../package-lock.json', import.meta.url), 'utf8'))

test('versões de manifesto e lockfile coincidem', () => {
  assert.equal(lock.name, manifest.name)
  assert.equal(lock.version, manifest.version)
  assert.equal(lock.packages[''].version, manifest.version)
  assert.deepEqual(lock.packages[''].dependencies, manifest.dependencies)
  assert.deepEqual(lock.packages[''].devDependencies, manifest.devDependencies)
})

test('referências a picocolors usam somente a versão publicada 1.1.1', () => {
  const item = lock.packages['node_modules/picocolors']
  assert.equal(item.version, '1.1.1')
  assert.equal(item.resolved, 'https://registry.npmjs.org/picocolors/-/picocolors-1.1.1.tgz')
  assert.equal(item.integrity, 'sha512-xceH2snhtb5M9liqDsmEw56le376mTZkEX/jEb/RxNFyegNul7eNslCXP9FDj/Lcu0X8KEyMceP2ntpaHrDEVA==')
  assert.equal(lock.packages['node_modules/postcss'].dependencies.picocolors, '^1.1.1')
})

test('URLs de tarball são coerentes com as versões fixadas no lockfile', () => {
  for (const [path, entry] of Object.entries(lock.packages)) {
    if (!path || !entry.resolved?.startsWith('https://registry.npmjs.org/')) continue
    const pkgName = path.split('node_modules/').at(-1).split('/').at(-1)
    const url = new URL(entry.resolved)
    assert.equal(url.pathname.split('/').at(-1), `${pkgName}-${entry.version}.tgz`, path)
    assert.match(entry.integrity ?? '', /^sha512-[A-Za-z0-9+/]+={0,2}$/, path)
  }
})
