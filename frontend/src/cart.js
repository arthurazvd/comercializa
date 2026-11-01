/** Adiciona uma quantidade ao carrinho, consolidando o mesmo produto sem criar outra linha.
 * Retorna o carrinho original em caso de erro; a quantidade total nunca pode ultrapassar
 * o estoque vendável informado pelo servidor (inclui exclusão de lotes vencidos).
 */
export function addOrIncrementCartItem(items, product, quantity, key) {
  const increment = Number(quantity)
  const available = Number(product?.available_stock ?? product?.stock)
  if (!product || product.active === false || !Number.isInteger(increment) || increment < 1) {
    return { ok: false, reason: 'Escolha um produto e uma quantidade válida.', items }
  }
  const index = items.findIndex(item => Number(item.product) === Number(product.id))
  const existing = index < 0 ? 0 : Number(items[index].quantity)
  if (!Number.isInteger(existing) || existing < 0 || !Number.isFinite(available) || existing + increment > available) {
    return { ok: false, reason: `Estoque insuficiente. Disponíveis: ${available} un.; no carrinho: ${existing} un.`, items }
  }
  if (index >= 0) {
    return { ok: true, merged: true, items: items.map((item, i) => i === index ? { ...item, quantity: existing + increment } : item) }
  }
  return { ok: true, merged: false, items: [...items, { product: product.id, quantity: increment, key }] }
}
