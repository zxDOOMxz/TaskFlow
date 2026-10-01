import api from './client'

export interface UploadedFile {
  id: string
  workspace_id: string
  project_id?: string
  uploaded_by_id: string
  original_name: string
  storage_key: string
  mime_type: string
  size_bytes: number
  entity_type?: string
  entity_id?: string
  created_at: string
  url?: string
  uploaded_by: {
    id: string
    first_name: string
    last_name: string
  }
}

export const filesApi = {
  list: (workspaceSlug: string) => api.get<UploadedFile[]>(`/workspaces/${workspaceSlug}/files`),
  upload: (workspaceSlug: string, file: File, projectId?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (projectId) formData.append('project_id', projectId)
    return api.post<UploadedFile>(`/workspaces/${workspaceSlug}/files/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (workspaceSlug: string, fileId: string) =>
    api.delete(`/workspaces/${workspaceSlug}/files/${fileId}`),
}
