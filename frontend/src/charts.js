/** Agregações exclusivamente de apresentação; o backend calcula receita e descontos. */
export function sortedSaleOptions(products, query = '', limit = 60) {
  const term = query.trim().toLocaleLowerCase('pt-BR')
  return products.filter(p => {
    const eligible = p.active && Number(p.available_stock ?? p.stock) > 0
    const matches = !term || [p.name, p.sku, p.category_name].some(x => String(x ?? '').toLocaleLowerCase('pt-BR').includes(term))
    return eligible && matches
  }).sort((a, b) => a.name.localeCompare(b.name, 'pt-BR', { sensitivity: 'base', numeric: true })).slice(0, limit)
}

export const MOVEMENT_REASONS = [
  { value: 'recebimento', label: 'Recebimento de mercadoria', direction: 'in' },
  { value: 'devolucao', label: 'Devolução de cliente', direction: 'in' },
  { value: 'avaria', label: 'Avaria / quebra', direction: 'out' },
  { value: 'perda', label: 'Perda / descarte por vencimento', direction: 'out' },
  { value: 'inventario', label: 'Acerto de inventário', direction: 'both' },
  { value: 'outro', label: 'Outro (descrever)', direction: 'both' },
]

export function movementNote(reason, custom = '') {
  const item = MOVEMENT_REASONS.find(r => r.value === reason)
  if (!item || (reason === 'outro' && !custom.trim())) return ''
  return reason === 'outro' ? custom.trim() : `${item.label}${custom.trim() ? ` — ${custom.trim()}` : ''}`
}

export function periodDates(period, todayISO) {
  const end = new Date(`${todayISO}T12:00:00Z`)
  const start = new Date(end)
  if (period === '7d') start.setUTCDate(end.getUTCDate() - 6)
  else if (period === '30d') start.setUTCDate(end.getUTCDate() - 29)
  else if (period === '90d') start.setUTCDate(end.getUTCDate() - 89)
  else if (period === '12m') { start.setUTCDate(1); start.setUTCMonth(end.getUTCMonth() - 11) }
  else throw new Error('Período desconhecido')
  return { start: start.toISOString().slice(0, 10), end: todayISO }
}

export function aggregateDaily(days = [], granularity = 'day', measure = 'revenue') {
  const buckets = new Map()
  for (const row of days) {
    const date = String(row.date).slice(0, 10)
    if (!/^\d{4}-\d\d-\d\d$/.test(date)) continue
    let label = date
    if (granularity === 'month') label = date.slice(0, 7)
    if (granularity === 'week') {
      const d = new Date(`${date}T12:00:00Z`)
      d.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7))
      label = d.toISOString().slice(0, 10)
    }
    buckets.set(label, (buckets.get(label) || 0) + Number(row[measure] || 0))
  }
  return [...buckets.entries()].sort(([a], [b]) => a.localeCompare(b))
    .map(([label, value]) => ({ label, value: Math.round(value * 100) / 100 }))
}

export function productChartData(products = [], measure = 'quantity', limit = 8) {
  return [...products].sort((a, b) => Number(b[measure]) - Number(a[measure]))
    .slice(0, limit).map(row => ({ label: row.name, value: Number(row[measure] || 0) }))
}

/** Mostra somente os N produtos mais vendidos no gráfico e no ranking.
 * Não inclui um segmento "Outros": os percentuais referem-se apenas ao Top N.
 */
export function rankingDonutRows(products = [], measure = 'quantity', limit = 10) {
  return [...products].filter(p => Number(p[measure]) > 0)
    .sort((a, b) => Number(b[measure]) - Number(a[measure]) || String(a.name).localeCompare(String(b.name), 'pt-BR'))
    .slice(0, limit).map(row => ({ label: row.name, value: Number(row[measure]) }))
}

export function concentrationPercentage(categories = []) {
  const values = categories.map(c => Number(c.revenue || 0)).filter(v => v > 0)
  const total = values.reduce((a, b) => a + b, 0)
  return total ? Math.round(100 * Math.max(...values) / total) : 0
}
