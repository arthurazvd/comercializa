/** Regras de apresentação e validação compartilhadas pela interface. */
export function formatMoney(value) {
  return Number(value || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
}

export function localDateISO(now = new Date()) {
  const pad = n => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

export function eligibleProducts(products, dateISO = localDateISO()) {
  return products.filter(p => p.active && p.stock > 0 && (!p.expiration_date || p.expiration_date >= dateISO))
}

export function calculateCart(items, products, discount = 0) {
  const subtotal = items.reduce((sum, item) => {
    const p = products.find(x => x.id === Number(item.product))
    return sum + Number(p?.sale_price || 0) * Number(item.quantity || 0)
  }, 0)
  return { subtotal, total: Math.max(0, subtotal - Number(discount || 0)) }
}

export function validCart(items, products, discount = 0, dateISO = localDateISO()) {
  if (!items.length) return false
  const eligible = eligibleProducts(products, dateISO)
  const ids = items.map(item => String(item.product))
  const { subtotal } = calculateCart(items, products, discount)
  return new Set(ids).size === ids.length
    && items.every(item => {
      const product = eligible.find(p => p.id === Number(item.product))
      const qty = Number(item.quantity)
      return product && Number.isInteger(qty) && qty > 0 && qty <= product.stock
    })
    && Number.isFinite(Number(discount)) && Number(discount) >= 0 && Number(discount) <= subtotal
}
