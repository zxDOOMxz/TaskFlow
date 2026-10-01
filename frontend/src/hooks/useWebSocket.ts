import { useEffect, useRef, useState } from 'react'

interface UseWebSocketOptions {
  roomId: string
  token: string
  onMessage?: (data: any) => void
  onConnect?: () => void
  onDisconnect?: () => void
}

export function useWebSocket({ roomId, token, onMessage, onConnect, onDisconnect }: UseWebSocketOptions) {
  const ws = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!roomId || !token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_WS_HOST || window.location.host
    const url = `${protocol}//${host}/ws/${roomId}?token=${token}`

    const socket = new WebSocket(url)
    ws.current = socket

    socket.onopen = () => {
      setIsConnected(true)
      setError(null)
      onConnect?.()
    }

    socket.onclose = () => {
      setIsConnected(false)
      onDisconnect?.()
    }

    socket.onerror = () => {
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

    return () => {
      socket.close()
    }
  }, [roomId, token])

  const sendMessage = (data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data))
    }
  }

  return { isConnected, error, sendMessage }
}
