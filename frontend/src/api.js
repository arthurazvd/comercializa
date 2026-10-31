import axios from 'axios'

// Em desenvolvimento Vite encaminha /api/ ao Django.
// No Cloudflare, configure VITE_API_URL=https://SEU-SERVICO.onrender.com/api/
const configured = (import.meta.env.VITE_API_URL || '').trim()
const apiBaseURL = configured ? `${configured.replace(/\/+$/, '')}/` : '/api/'
const TOKEN_KEY = 'comercializa_auth_token'

export function getAuthToken() {
  try { return window.sessionStorage.getItem(TOKEN_KEY) || '' } catch { return '' }
}
export function saveAuthToken(token) {
  try { window.sessionStorage.setItem(TOKEN_KEY, token) } catch { /* sem armazenamento */ }
}
export function clearAuthToken() {
  try { window.sessionStorage.removeItem(TOKEN_KEY) } catch { /* sem armazenamento */ }
}

// No Render Free, uma primeira requisição pode aguardar o serviço despertar.
// Os writes usam um tempo maior e NÃO são repetidos sem a mesma chave idempotente.
export const api = axios.create({ baseURL: apiBaseURL, timeout: 110000 })

api.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

const transientStatuses = new Set([502, 503, 504])
export function isTransientFailure(error) {
  if (axios.isCancel(error)) return false
  return !error?.response || transientStatuses.has(error.response.status)
}

api.interceptors.response.use(
  response => response,
  async error => {
    const endpoint = String(error?.config?.url || '')
    if (error?.response?.status === 401 && !endpoint.startsWith('auth/login/')) {
      clearAuthToken()
      if (typeof window !== 'undefined') window.dispatchEvent(new Event('comercializa:unauthorized'))
    }
    // Apenas leituras são repetidas automaticamente. POSTs usam chave persistida
    // por operação, no helper abaixo, para nunca duplicar venda/cadastro.
    const config = error?.config
    if (config?.method?.toLowerCase() === 'get' && isTransientFailure(error)
        && (config.__readRetry || 0) < 1) {
      config.__readRetry = (config.__readRetry || 0) + 1
      await new Promise(resolve => setTimeout(resolve, 800))
      return api.request(config)
    }
    return Promise.reject(error)
  },
)

const pendingPosts = new Map()
function newOperationId() {
  return globalThis.crypto?.randomUUID?.() || `op_${Date.now()}_${Math.random().toString(36).slice(2)}_${Math.random().toString(36).slice(2)}`
}

/** Uma operação reenvia sempre o MESMO identificador se a conexão se perder.
 * A transação do backend armazena a resposta, devolvendo-a no segundo envio.
 * Somente 400/401/403/404/409/422 definitivos liberam a chave.
 */
export async function postWithRecovery(url, payload) {
  const signature = `${url}:${JSON.stringify(payload)}`
  let key = pendingPosts.get(signature)
  if (!key) {
    key = newOperationId()
    pendingPosts.set(signature, key)
  }
  const config = { headers: { 'Idempotency-Key': key }, timeout: 120000 }
  try {
    let response
    try {
      response = await api.post(url, payload, config)
    } catch (error) {
      if (!isTransientFailure(error)) throw error
      await new Promise(resolve => setTimeout(resolve, 900))
      response = await api.post(url, payload, config)
    }
    pendingPosts.delete(signature)
    return response
  } catch (error) {
    if (!isTransientFailure(error)) pendingPosts.delete(signature)
    throw error
  }
}

export function writeErrorText(error, standardMessage) {
  if (isTransientFailure(error)) {
    return 'Não foi possível confirmar a operação. Ela pode ter sido salva! Confira a lista antes de refazer. Se repetir sem mudar os dados, o sistema reutiliza a mesma operação.'
  }
  return standardMessage(error)
}
