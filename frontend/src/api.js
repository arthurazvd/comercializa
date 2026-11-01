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
  for (const job of backgroundConfirmations.values()) job.active = false
  backgroundConfirmations.clear()
  try { window.sessionStorage.setItem(TOKEN_KEY, token) } catch { /* sem armazenamento */ }
}
export function clearAuthToken() {
  pendingPosts.clear()
  for (const job of backgroundConfirmations.values()) job.active = false
  backgroundConfirmations.clear()
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
  // Exceções de Vue/JavaScript não são falhas de rede. Essa distinção evita
  // informar que um POST 201 falhou se a interface lançar um TypeError depois.
  if (axios.isCancel(error) || !axios.isAxiosError(error)) return false
  if (error.response) return transientStatuses.has(error.response.status)
  return ['ECONNABORTED', 'ETIMEDOUT', 'ERR_NETWORK'].includes(error.code)
}

export function isWritePending(error) {
  return error?.code === 'COMERCIALIZA_WRITE_PENDING'
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
const backgroundConfirmations = new Map()

function finishPendingOperation(signature, storedName) {
  pendingPosts.delete(signature)
  setPendingStorage(storedName, null)
  const pending = backgroundConfirmations.get(signature)
  if (pending) {
    pending.active = false
    backgroundConfirmations.delete(signature)
  }
}

function continueConfirmation(url, key, signature, storedName, onConfirmedLater) {
  if (typeof onConfirmedLater !== 'function') return
  if (backgroundConfirmations.has(signature)) return
  const job = { active: true }
  backgroundConfirmations.set(signature, job)
  // Nunca reenvia uma escrita automaticamente nesta fase: consulta apenas o
  // comprovante da operação já gravado, usando a mesma chave idempotente.
  void (async () => {
    for (const delay of [1500, 3000, 6000, 12000, 24000, 48000]) {
      await new Promise(resolve => setTimeout(resolve, delay))
      if (!job.active) break
      try {
        const response = await findConfirmedPost(url, key)
        if (response && job.active) {
          finishPendingOperation(signature, storedName)
          onConfirmedLater(response)
          return
        }
      } catch (error) {
        if (error?.response?.status === 401 || error?.response?.status === 403) break
      }
    }
    if (backgroundConfirmations.get(signature) === job) backgroundConfirmations.delete(signature)
  })().catch(error => {
    console.warn('Falha durante a confirmação posterior:', error)
    if (backgroundConfirmations.get(signature) === job) backgroundConfirmations.delete(signature)
  })
}

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
export async function postWithRecovery(url, payload, { onConfirmedLater } = {}) {
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
    finishPendingOperation(signature, storedName)
    return response
  } catch (error) {
    if (isTransientFailure(error)) {
      // A resposta pode ter sido perdida DEPOIS do commit. Não exibir um
      // pop-up vermelho de erro: verificar a operação em segundo plano.
      continueConfirmation(url, key, signature, storedName, onConfirmedLater)
      const pending = new Error('Confirmação pendente no servidor.', { cause: error })
      pending.code = 'COMERCIALIZA_WRITE_PENDING'
      throw pending
    }
    finishPendingOperation(signature, storedName)
    throw error
  }
}

export function writeErrorText(error, standardMessage) {
  // Estado desconhecido não equivale a erro de gravação. Não mostrar um
  // alerta falso, especialmente quando o POST terminou com 201 no servidor.
  if (isWritePending(error)) return ''
  return standardMessage(error)
}
