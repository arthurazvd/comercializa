import axios from 'axios'

// Em desenvolvimento, o Vite encaminha /api para o backend Django.
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/',
  timeout: 12000,
})
