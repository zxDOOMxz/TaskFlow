import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { AuthProvider } from './context/AuthContext'
import { ErrorBoundary } from './components/ErrorBoundary'
import './index.css'

console.log('[MAIN] main.tsx module executing')

const requiredEnv = ['VITE_SUPABASE_URL', 'VITE_SUPABASE_ANON_KEY']
const missing = requiredEnv.filter((key) => !import.meta.env[key])

console.log('[MAIN] missing env vars:', missing)

if (missing.length > 0) {
  console.error('[MAIN] Rendering missing env error')
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <h1 className="text-xl font-bold text-red-600 mb-4">Ошибка конфигурации</h1>
        <p className="text-slate-600 mb-4">
          Не заданы обязательные переменные окружения для сборки frontend:
        </p>
        <ul className="list-disc pl-5 text-slate-700 space-y-1 mb-4">
          {missing.map((key) => (
            <li key={key}>
              <code>{key}</code>
            </li>
          ))}
        </ul>
        <p className="text-sm text-slate-500">
          Добавьте их в разделе Environment variables настроек сайта в Netlify и пересоберите деплой.
        </p>
      </div>
    </div>
  )
} else {
  console.log('[MAIN] Rendering app')
  ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </React.StrictMode>,
  )
}
