import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'

const app = readFileSync(new URL('../src/App.vue', import.meta.url), 'utf8')
const css = readFileSync(new URL('../src/style.css', import.meta.url), 'utf8')
const version = readFileSync(new URL('../src/version.js', import.meta.url), 'utf8')

test('V1.4.0 shows profit gross COGS expenses and purchases distinctly', () => {
  assert.match(app, /finance\.summary\.gross_profit/)
  assert.match(app, /finance\.summary\.cogs/)
  assert.match(app, /finance\.summary\.expense_total/)
  assert.match(app, /finance\.summary\.purchase_total/)
  assert.match(app, /finance\.summary\.operating_result/)
  assert.match(app, /não é fluxo de caixa nem lucro líquido contábil/)
})

test('financial entry form can register expense or investment and void', () => {
  assert.match(app, /recordFinancialEntry/)
  assert.match(app, /voidFinancialEntry/)
  assert.match(app, /postWithRecovery\('finance\/entries\//)
  assert.match(app, /finance\/entries\/\$\{entry\.id\}\/void\//)
  assert.match(app, /type="date" required/)
})

test('financial section is responsive and version is semver', () => {
  assert.match(css, /financial-kpis/)
  assert.match(css, /financial-entry-row/)
  assert.match(css, /@media\(max-width:560px\)/)
  assert.match(version, /\b1\.5\.0\b/)
})
