import { createClient, SupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

let supabase: SupabaseClient

if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    'Supabase URL or anon key is missing. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.'
  )
  // Create a stub that will throw on usage so the app can still render.
    supabase = new Proxy({} as SupabaseClient, {
      get() {
        return () => {
          throw new Error(
            `Supabase is not configured (missing ${!supabaseUrl ? 'VITE_SUPABASE_URL' : 'VITE_SUPABASE_ANON_KEY'}).`
          )
        }
      },
    })
} else {
  supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  })
}

export { supabase }

export type { SupabaseClient }
