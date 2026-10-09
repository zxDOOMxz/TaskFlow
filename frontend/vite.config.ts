import { defineConfig, Plugin } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { viteSingleFile } from 'vite-plugin-singlefile'

function removeInlineCrossorigin(): Plugin {
  return {
    name: 'remove-inline-crossorigin',
    enforce: 'post',
    transformIndexHtml(html) {
      // Remove crossorigin attribute from inline module scripts
      return html.replace(/<script type="module" crossorigin>/g, '<script type="module">')
    },
  }
}

export default defineConfig({
  plugins: [react(), viteSingleFile(), removeInlineCrossorigin()],
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
