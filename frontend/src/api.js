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
// Mantemos só a chave de idempotência: sem polling, sem consulta adicional de
// "comprovação" e sem repetição automática de escritas.
function finishPendingOperation(signature, storedName) {
  pendingPosts.delete(signature)
  setPendingStorage(storedName, null)
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

/**
 * Um único POST por clique. HTTP 2xx é sucesso definitivo; nenhum GET extra é
 * exigido para "confirmar". Se a conexão cair antes da resposta, preservamos a
 * mesma Idempotency-Key para um eventual clique posterior, sem duplicar dados.
 * Não afirmamos sucesso nem erro quando a resposta não chegou.
 */
export async function postWithRecovery(url, payload, { timeout = 95000 } = {}) {
  const signature = `${url}:${JSON.stringify(payload)}`
  const storedName = await pendingStorageName(signature)
  const key = pendingPosts.get(signature) || pendingFromStorage(storedName) || newOperationId()
  pendingPosts.set(signature, key)
  setPendingStorage(storedName, key)
  try {
    const response = await api.post(url, payload, {
      headers: { 'Idempotency-Key': key },
      timeout,
    })
    // Axios resolve somente os status de sucesso (2xx).
    finishPendingOperation(signature, storedName)
    return response
  } catch (error) {
    if (isTransientFailure(error) || (axios.isAxiosError(error) && Number(error.response?.status) >= 500)) {
      // O servidor pode ter gravado: não repetir POST automaticamente.
      // Se o usuário enviar o mesmo formulário, a API recebe a mesma chave.
      const uncertain = new Error('Resposta não recebida.', { cause: error })
      uncertain.code = 'COMERCIALIZA_WRITE_PENDING'
      throw uncertain
    }
    finishPendingOperation(signature, storedName)
    throw error
  }
}

export function writeErrorText(error, standardMessage) {
  // Falha de transporte sem resposta HTTP não prova falha do cadastro.
  if (isWritePending(error)) return ''
  return standardMessage(error)
}
