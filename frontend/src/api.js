import axios from 'axios'

// Em desenvolvimento, Vite encaminha /api/ ao Django.
// No Cloudflare, defina VITE_API_URL=https://SEU-SERVICO.onrender.com/api/
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

export const api = axios.create({ baseURL: apiBaseURL, timeout: 65000 })

api.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    const endpoint = String(error?.config?.url || '')
    if (error?.response?.status === 401 && !endpoint.startsWith('auth/login/')) {
      clearAuthToken()
      if (typeof window !== 'undefined') window.dispatchEvent(new Event('comercializa:unauthorized'))
    }
    return Promise.reject(error)
  },
)
