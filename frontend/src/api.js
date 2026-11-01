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
  pendingPosts.clear()
  try { window.sessionStorage.setItem(TOKEN_KEY, token) } catch { /* sem armazenamento */ }
}
export function clearAuthToken() {
  pendingPosts.clear()
  try { window.sessionStorage.removeItem(TOKEN_KEY) } catch { /* sem armazenamento */ }
}

// No Render Free, uma primeira requisição pode aguardar o serviço despertar.
// Os writes usam um tempo maior e NÃO são repetidos sem a mesma chave idempotente.
export const api = axios.create({ baseURL: apiBaseURL, timeout: 110000 })

api.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Token ${token}`
  // Evita relatórios e listas antigas servidos pelo cache do navegador/proxy.
  if (config.method?.toLowerCase() === 'get') {
    config.params = { ...(config.params || {}), __fresh: Date.now() }
  }
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
// A sessão guarda apenas UUID + hash de uma operação não confirmada (nunca
// produto, venda ou senha). Assim, atualizar a página não perde a chave.
async function pendingStorageName(signature) {
  if (!globalThis.crypto?.subtle || !globalThis.TextEncoder) return ''
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${getAuthToken()}|${signature}`))
  return `comercializa_op_${Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2, '0')).join('')}`
}
function pendingFromStorage(name) {
  if (!name) return null
  try {
    const item = JSON.parse(window.sessionStorage.getItem(name) || 'null')
    if (item?.key && Number.isFinite(item.at) && Date.now() - item.at < 86400000) return item.key
    window.sessionStorage.removeItem(name)
  } catch { /* armazenamento indisponível */ }
  return null
}
function setPendingStorage(name, key) {
  if (!name) return
  try {
    if (key) window.sessionStorage.setItem(name, JSON.stringify({ key, at: Date.now() }))
    else window.sessionStorage.removeItem(name)
  } catch { /* armazenamento indisponível */ }
}
function newOperationId() {
  return globalThis.crypto?.randomUUID?.() || `op_${Date.now()}_${Math.random().toString(36).slice(2)}_${Math.random().toString(36).slice(2)}`
}

/** Confirma no banco a operação que pode ter sido concluída sem resposta HTTP. */
async function findConfirmedPost(url, key) {
  try {
    const { data } = await api.get(`operations/${key}/`, {
      timeout: 20000, __readRetry: 1,
    })
    const normalizedPath = `/api/${url.replace(/^\/+/, '')}`
    if (data?.confirmed && data.path === normalizedPath && data.status >= 200 && data.status < 300) {
      return { data: data.data, status: data.status, headers: { 'x-operation-confirmed': 'true' } }
    }
  } catch (error) {
    if (error?.response?.status === 401 || error?.response?.status === 403) throw error
    // 404 = operação ainda não confirmada. Em falha de rede, o POST seguinte
    // reutiliza a mesma chave; a API garante execução única no banco.
  }
  return null
}

/** Reenvio seguro: consulta a confirmação persistida antes de repetir um POST.
 * A chave fica pendente em caso de interrupção, não é descartada por timeout.
 */
export async function postWithRecovery(url, payload) {
  const signature = `${url}:${JSON.stringify(payload)}`
  const storedName = await pendingStorageName(signature)
  const oldKey = pendingFromStorage(storedName)
  let key = pendingPosts.get(signature) || oldKey
  const resumed = Boolean(oldKey)
  if (!key) key = newOperationId()
  pendingPosts.set(signature, key)
  setPendingStorage(storedName, key)
  const config = { headers: { 'Idempotency-Key': key }, timeout: 95000 }
  try {
    let response = resumed ? await findConfirmedPost(url, key) : null
    try {
      if (!response) response = await api.post(url, payload, config)
    } catch (error) {
      if (!isTransientFailure(error)) throw error
      response = await findConfirmedPost(url, key)
      if (!response) {
        try {
          response = await api.post(url, payload, config)
        } catch (retryError) {
          if (!isTransientFailure(retryError)) throw retryError
          response = await findConfirmedPost(url, key)
          if (!response) throw retryError
        }
      }
    }
    pendingPosts.delete(signature)
    setPendingStorage(storedName, null)
    return response
  } catch (error) {
    if (!isTransientFailure(error)) {
      pendingPosts.delete(signature)
      setPendingStorage(storedName, null)
    }
    throw error
  }
}

export function writeErrorText(error, standardMessage) {
  if (isTransientFailure(error)) {
    return 'Não foi possível confirmar a operação. Ela pode ter sido salva! Confira a lista antes de refazer. Se repetir sem mudar os dados, o sistema reutiliza a mesma operação.'
  }
  return standardMessage(error)
}
