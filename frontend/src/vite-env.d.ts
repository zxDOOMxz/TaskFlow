/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_HOST: string
  readonly VITE_SUPABASE_URL: string
  readonly VITE_SUPABASE_ANON_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// Базовый путь приложения с завершающим слешем: "/" или "/TaskFlow/".
// Задаётся через define в vite.config.ts (import.meta.env.BASE_URL не подходит: singlefile ставит base "./").
declare const __APP_BASE__: string
