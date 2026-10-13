import { useEffect, useRef, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface UseWebSocketOptions {
  roomId: string
  token?: string
  onMessage?: (data: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

// Хост WS: явный VITE_WS_HOST, либо хост абсолютного VITE_API_URL (например, Render при хостинге фронта на GitHub Pages),
// либо текущий хост при относительном VITE_API_URL (/api/v1 через nginx).
function resolveWsHost(): string {
  const explicit = import.meta.env.VITE_WS_HOST
  if (explicit) return explicit
  const api = import.meta.env.VITE_API_URL || ''
  if (/^https?:\/\//.test(api)) return new URL(api).host
  return window.location.host
}

export function useWebSocket({ roomId, token, onMessage, onConnect, onDisconnect }: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!roomId) return

    let socket: WebSocket | null = null
    let cancelled = false

    const connect = async () => {
      let accessToken = token
      if (!accessToken) {
        try {
          const { data } = await supabase.auth.getSession()
          accessToken = data.session?.access_token || ''
        } catch (err) {
          console.error('Failed to get session for WebSocket:', err)
        }
      }
      if (!accessToken || cancelled) return

      const host = resolveWsHost()
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const url = `${protocol}//${host}/ws/${roomId}?token=${accessToken}`

      socket = new WebSocket(url)
      ws.current = socket

      socket.onopen = () => {
        if (cancelled) return
        setIsConnected(true)
        setError(null)
        onConnect?.()
      }

      socket.onclose = () => {
        if (cancelled) return
        setIsConnected(false)
        onDisconnect?.()
      }

      socket.onerror = () => {
        if (cancelled) return
        setError('WebSocket error')
        setIsConnected(false)
      }

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }
    }

    connect().catch((err) => {
      console.error('WebSocket connect failed:', err)
      if (!cancelled) setError('WebSocket connect failed')
    })

    return () => {
      cancelled = true
      socket?.close()
    }
  }, [roomId, token])

  const sendMessage = (data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    }
  }

  return { isConnected, error, sendMessage }
}
