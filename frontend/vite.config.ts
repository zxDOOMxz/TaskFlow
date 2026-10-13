import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { viteSingleFile } from 'vite-plugin-singlefile'

// BASE_PATH задаётся в CI для GitHub Pages project page, например "/TaskFlow/".
// Локально и в Docker остаётся "/".
// vite-plugin-singlefile принудительно ставит base "./", поэтому путь передаём через define.
const appBase = process.env.BASE_PATH || '/'

export default defineConfig({
  define: {
    __APP_BASE__: JSON.stringify(appBase.endsWith('/') ? appBase : appBase + '/'),
  },
  plugins: [react(), viteSingleFile()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    sourcemap: false,
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
