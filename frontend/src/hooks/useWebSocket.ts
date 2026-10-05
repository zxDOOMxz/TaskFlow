import { useEffect, useRef, useState } from 'react'
import { supabase } from '@/lib/supabase'

interface UseWebSocketOptions {
  roomId: string
  token?: string
  onMessage?: (data: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
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
      if (!accessToken) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = import.meta.env.VITE_WS_HOST || window.location.host
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

    connect()

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
