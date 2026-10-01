import api from './client'
import { MessageRead, RoomCreate, RoomDetail } from '@/types'

export const chatApi = {
  listRooms: (workspaceSlug: string) => api.get<RoomDetail[]>(`/workspaces/${workspaceSlug}/chat/rooms`),
  createRoom: (workspaceSlug: string, data: RoomCreate) =>
    api.post(`/workspaces/${workspaceSlug}/chat/rooms`, data),
  listMessages: (workspaceSlug: string, roomId: string) =>
    api.get<MessageRead[]>(`/workspaces/${workspaceSlug}/chat/rooms/${roomId}/messages`),
  sendMessage: (workspaceSlug: string, roomId: string, content: string) =>
    api.post<MessageRead>(`/workspaces/${workspaceSlug}/chat/rooms/${roomId}/messages`, { content }),
}
