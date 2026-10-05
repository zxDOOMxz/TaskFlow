import { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { chatApi } from '@/api/chat'
import { useWebSocket } from '@/hooks/useWebSocket'
import { MentionRenderer } from '@/components/common/MentionRenderer'
import { MessageRead, RoomDetail } from '@/types'

interface ChatPanelProps {
  workspaceSlug: string
  roomId: string
}

export function ChatPanel({ workspaceSlug, roomId }: ChatPanelProps) {
  const { user } = useAuthStore()
  const [messages, setMessages] = useState<MessageRead[]>([])
  const [input, setInput] = useState('')
  const [room, setRoom] = useState<RoomDetail | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    chatApi.listMessages(workspaceSlug, roomId).then((res) => {
      setMessages(res.data.reverse())
    })
    chatApi.listRooms(workspaceSlug).then((res) => {
      const r = res.data.find((room) => room.id === roomId)
      if (r) setRoom(r)
    })
  }, [workspaceSlug, roomId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const { isConnected } = useWebSocket({
    roomId: `room:${roomId}`,
    onMessage: (data) => {
      if (data.type === 'new_message') {
        setMessages((prev) => {
          if (prev.some((m) => m.id === data.data.id)) return prev
          return [...prev, data.data]
        })
      }
    },
  })

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    const text = input.trim()
    if (!text) return
    setInput('')
    try {
      const { data } = await chatApi.sendMessage(workspaceSlug, roomId, text)
      setMessages((prev) => {
        if (prev.some((m) => m.id === data.id)) return prev
        return [...prev, data]
      })
    } catch (err) {
      console.error('Failed to send message:', err)
    }
  }

  return (
    <div className="flex flex-col h-full bg-white border-l border-slate-200 w-80">
      <div className="p-3 border-b border-slate-200">
        <h3 className="font-semibold text-slate-900 truncate">
          {room?.name || 'Чат'}
        </h3>
        <p className="text-xs text-slate-500">
          {isConnected ? 'Подключено' : 'Подключение...'}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${
              msg.author_id === user?.id ? 'items-end' : 'items-start'
            }`}
          >
            <div
              className={`max-w-[85%] px-3 py-2 rounded-lg text-sm ${
                msg.author_id === user?.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-slate-100 text-slate-900'
              }`}
            >
              <MentionRenderer text={msg.content} workspaceSlug={workspaceSlug} />
            </div>
            <span className="text-xs text-slate-400 mt-1">
              {msg.author.first_name} {msg.author.last_name}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSend} className="p-3 border-t border-slate-200 flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Написать сообщение..."
          className="flex-1"
        />
        <Button type="submit" size="sm">
          →
        </Button>
      </form>
    </div>
  )
}
