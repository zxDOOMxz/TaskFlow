import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { chatApi } from '@/api/chat'
import { RoomDetail } from '@/types'

export function ChatPage() {
  const { workspaceSlug } = useParams()
  const [rooms, setRooms] = useState<RoomDetail[]>([])
  const [selectedRoomId, setSelectedRoomId] = useState<string | null>(null)

  useEffect(() => {
    if (!workspaceSlug) return
    chatApi.listRooms(workspaceSlug).then((res) => {
      setRooms(res.data)
      if (res.data.length > 0 && !selectedRoomId) {
        setSelectedRoomId(res.data[0].id)
      }
    })
  }, [workspaceSlug])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="Чаты" />
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-white border-r border-slate-200 overflow-y-auto">
          <div className="p-3 border-b border-slate-200">
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Комнаты
            </h3>
          </div>
          {rooms.length === 0 ? (
            <p className="p-3 text-sm text-slate-400">Нет чатов</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {rooms.map((room) => (
                <li
                  key={room.id}
                  onClick={() => setSelectedRoomId(room.id)}
                  className={`p-3 cursor-pointer hover:bg-slate-50 ${
                    selectedRoomId === room.id ? 'bg-primary-50' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {room.name || 'Без названия'}
                  </p>
                  {room.last_message && (
                    <p className="text-xs text-slate-500 truncate">
                      {room.last_message.content}
                    </p>
                  )}
                  {room.unread_count > 0 && (
                    <span className="inline-flex items-center justify-center px-2 py-0.5 mt-1 text-xs font-medium text-white bg-primary-600 rounded-full">
                      {room.unread_count}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </aside>

        <main className="flex-1 flex overflow-hidden">
          {selectedRoomId && workspaceSlug ? (
            <ChatPanel workspaceSlug={workspaceSlug} roomId={selectedRoomId} />
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400">
              Выберите чат
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
