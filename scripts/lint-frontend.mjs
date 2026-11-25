import { readdirSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { readFileSync } from 'node:fs'
import compiler from '../frontend/node_modules/@vue/compiler-sfc/dist/compiler-sfc.cjs.js'
const { parse, compileScript, compileTemplate } = compiler
const root = fileURLToPath(new URL('../frontend/', import.meta.url))
function walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const file = join(dir, entry.name)
    if (entry.isDirectory()) walk(file)
    else if (/\.(js|mjs)$/.test(file)) execFileSync(process.execPath, ['--check', file], { stdio: 'inherit' })
    else if (file.endsWith('.vue')) {
      const { descriptor, errors } = parse(readFileSync(file, 'utf8'), { filename: file })
      if (errors.length) throw new Error(`${file}: ${errors.join('; ')}`)
      if (descriptor.script || descriptor.scriptSetup) compileScript(descriptor, { id: file })
      if (descriptor.template) {
        const result = compileTemplate({ source: descriptor.template.content, filename: file, id: file })
        if (result.errors.length) throw new Error(`${file}: ${result.errors.join('; ')}`)
      }
    }
  }
}
walk(join(root, 'src'))
walk(join(root, 'tests'))
console.log('Validação estática JavaScript/Vue concluída.')
