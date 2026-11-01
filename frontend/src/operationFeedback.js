/** Apenas erros de validação/permissão HTTP explicitamente informados pela API.
 * Timeout, falha CORS, conexão interrompida, exceção de UI e erros 5xx não
 * autorizam declarar que uma operação foi rejeitada: ela pode ter sido gravada.
 */
export function actionableWriteMessage(error) {
  const status = Number(error?.response?.status)
  if (![400, 403, 404, 409, 422].includes(status)) return ''
  const data = error?.response?.data
  if (!data) return ''
  if (typeof data === 'string') return data.trim().slice(0, 350)
  if (typeof data !== 'object') return ''
  if (typeof data.detail === 'string') return data.detail.trim().slice(0, 350)
  const items = Object.entries(data)
    .filter(([, value]) => value != null)
    .map(([field, value]) => {
      const detail = Array.isArray(value) ? value.join(', ') : typeof value === 'string' ? value : ''
      return detail ? `${field}: ${detail}` : ''
    }).filter(Boolean)
  return items.join(' · ').slice(0, 350)
}
