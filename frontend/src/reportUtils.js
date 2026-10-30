import { localDateISO } from './utils.js'

export const defaultReportFilters = (now = new Date()) => ({
  start: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`,
  end: localDateISO(now),
  category: '', product: '',
})

export function queryReport(filters) {
  const params = new URLSearchParams({ start: filters.start, end: filters.end })
  if (filters.category) params.set('category', String(filters.category))
  if (filters.product) params.set('product', String(filters.product))
  return params.toString()
}

export function inventoryStatus(product, dateISO = localDateISO()) {
  if (!product.active) return 'inativo'
  if (Number(product.expired_units ?? 0) > 0 || (product.expired_units === undefined && product.stock > 0 && product.expiration_date && product.expiration_date < dateISO)) return 'vencido'
  const limit = new Date(`${dateISO}T12:00:00`)
  limit.setDate(limit.getDate() + 15)
  if (Number(product.expiring_units ?? 0) > 0 || (product.expiring_units === undefined && product.stock > 0 && product.expiration_date && product.expiration_date <= localDateISO(limit))) return 'a_vencer'
  if (Number(product.available_stock ?? product.stock) <= product.minimum_stock) return 'critico'
  return 'normal'
}

export function matchProductSearch(product, term) {
  const normalized = term.trim().toLocaleLowerCase('pt-BR')
  return !normalized || [product.name, product.sku, product.category_name, product.category]
    .some(value => String(value ?? '').toLocaleLowerCase('pt-BR').includes(normalized))
}

export function filteredInventory(products, term = '', status = 'all', category = '') {
  return products.filter(p => {
    if (!matchProductSearch(p, term)) return false
    if (category && String(p.category) !== String(category)) return false
    if (status === 'all') return true
    if (status === 'critico') return p.active && Number(p.available_stock ?? p.stock) <= p.minimum_stock
    if (status === 'a_vencer' || status === 'vencido') return inventoryStatus(p) === status
    return inventoryStatus(p) === status
  })
}
