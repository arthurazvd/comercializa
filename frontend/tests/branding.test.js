import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { BRAND_ASSETS, getCopyrightYear } from '../src/branding.js'

const root = join(dirname(fileURLToPath(import.meta.url)), '..')
const file = path => readFileSync(join(root, path), 'utf8')
const viewBox = svg => svg.match(/viewBox="([^"]+)"/)?.[1].split(' ').map(Number)

test('ano de copyright acompanha automaticamente a data corrente', () => {
  assert.equal(getCopyrightYear(new Date('2026-12-31T12:00:00')), 2026)
  assert.equal(getCopyrightYear(new Date('2027-01-01T12:00:00')), 2027)
  assert.equal(getCopyrightYear(new Date('2032-07-01T12:00:00')), 2032)
})

test('todas as variações da identidade visual são SVGs existentes e têm viewBox válido', () => {
  for (const path of Object.values(BRAND_ASSETS)) {
    assert.ok(existsSync(join(root, 'public', path)), `Arquivo ausente: ${path}`)
    const svg = file(join('public', path))
    assert.match(svg, /<svg\b/)
    const bounds = viewBox(svg)
    assert.equal(bounds?.length, 4, `viewBox inválido: ${path}`)
    assert.ok(bounds.every(Number.isFinite) && bounds[2] > 0 && bounds[3] > 0)
  }
})

test('favicon usa somente o símbolo vetorial, sem o nome da marca', () => {
  for (const path of [BRAND_ASSETS.faviconOnLight, BRAND_ASSETS.faviconOnDark]) {
    const svg = file(join('public', path)).replace(/<defs>[\s\S]*?<\/defs>/, '')
    assert.doesNotMatch(svg, /<text\b|<image\b/)
    assert.match(svg, /<g\b/)
    assert.doesNotMatch(svg, /<path[^>]*d="M-1[3-9]\d{2}/) // desenho da palavra na variante horizontal
  }
})

test('horizontal é paisagem e vertical é retrato, sem distorção de proporção', () => {
  assert.ok(viewBox(file('public' + BRAND_ASSETS.horizontalOnDark))[2] / viewBox(file('public' + BRAND_ASSETS.horizontalOnDark))[3] > 4)
  assert.ok(viewBox(file('public' + BRAND_ASSETS.horizontalOnLight))[2] / viewBox(file('public' + BRAND_ASSETS.horizontalOnLight))[3] > 4)
  const [, , w, h] = viewBox(file('public' + BRAND_ASSETS.verticalOnDark))
  assert.ok(h > w)
})

test('HTML usa favicon claro/escuro e tela tem logos, rodapé e créditos', () => {
  const index = file('index.html')
  const app = file('src/App.vue')
  const css = file('src/style.css')
  assert.match(index, /favicon-comercializa\.svg/)
  assert.match(index, /favicon-comercializa-dark\.svg/)
  assert.match(index, /prefers-color-scheme: dark/)
  assert.match(app, /BRAND_ASSETS\.verticalOnDark/)
  assert.match(app, /BRAND_ASSETS\.horizontalOnDark/)
  assert.match(app, /BRAND_ASSETS\.horizontalOnLight/)
  assert.match(app, /Arthur Azevêdo/)
  assert.match(app, /Todos os direitos reservados/)
  assert.match(app, /\{\{ copyrightYear \}\}/)
  assert.match(css, /\.brand-logo-horizontal/)
  assert.match(css, /\.app-footer/)
})
