import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Evita publicar um site Cloudflare que aponta /api/ para o próprio frontend.
if (process.env.CF_PAGES === '1' && !process.env.VITE_API_URL) {
  throw new Error('Configure VITE_API_URL no Cloudflare Pages (ex.: https://seu-backend.onrender.com/api/) e gere novo deploy.')
}

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: true } },
  },
})
