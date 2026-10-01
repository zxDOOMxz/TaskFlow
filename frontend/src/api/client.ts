import axios from 'axios'
import { supabase } from '../lib/supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      // Supabase refreshes the session automatically; fetch a fresh one and retry.
      const { data } = await supabase.auth.getSession()
      const token = data.session?.access_token
      if (token) {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return api(originalRequest)
      }
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
