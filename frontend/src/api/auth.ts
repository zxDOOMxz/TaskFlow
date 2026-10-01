import api from './client'
import { User } from '@/types'

export interface LoginData {
  email: string
  password: string
}

export interface RegisterData extends LoginData {
  first_name: string
  last_name: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
}

export const authApi = {
  login: (data: LoginData) => api.post<TokenPair>('/auth/login', data),
  register: (data: RegisterData) => api.post<TokenPair>('/auth/register', data),
  me: () => api.get<User>('/auth/me'),
  refresh: (refresh_token: string) => api.post<TokenPair>('/auth/refresh', { refresh_token }),
}
