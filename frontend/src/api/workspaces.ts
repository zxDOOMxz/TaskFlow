import api from './client'
import { Project, Workspace } from '@/types'

export const workspaceApi = {
  list: () => api.get<Workspace[]>('/workspaces'),
  get: (slug: string) => api.get<Workspace>(`/workspaces/${slug}`),
  create: (data: { name: string }) => api.post<Workspace>('/workspaces', data),
  projects: (slug: string) => api.get<Project[]>(`/workspaces/${slug}/projects`),
}

export const projectApi = {
  get: (workspaceSlug: string, projectKey: string) =>
    api.get<Project>(`/workspaces/${workspaceSlug}/projects/${projectKey}`),
  create: (workspaceSlug: string, data: { key: string; name: string; description?: string }) =>
    api.post<Project>(`/workspaces/${workspaceSlug}/projects`, data),
  issues: (projectKey: string) => api.get(`/projects/${projectKey}/issues`),
  boards: (projectKey: string) => api.get(`/projects/${projectKey}/boards`),
  sprints: (projectKey: string) => api.get(`/projects/${projectKey}/sprints`),
}

export const issueApi = {
  create: (projectKey: string, data: object) =>
    api.post(`/projects/${projectKey}/issues`, data),
  update: (projectKey: string, issueKey: string, data: object) =>
    api.put(`/projects/${projectKey}/issues/${issueKey}`, data),
  get: (projectKey: string, issueKey: string) =>
    api.get(`/projects/${projectKey}/issues/${issueKey}`),
}
