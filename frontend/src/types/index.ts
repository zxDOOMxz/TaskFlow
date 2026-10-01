export interface User {
  id: string
  email: string
  first_name: string
  last_name: string
  avatar_url?: string
  timezone: string
  is_active: boolean
  created_at: string
}

export interface Workspace {
  id: string
  name: string
  slug: string
  logo_url?: string
  owner_id: string
  created_at: string
}

export interface WorkspaceMember {
  id: string
  user_id: string
  role: 'admin' | 'manager' | 'developer' | 'viewer'
  user: User
}

export interface Project {
  id: string
  workspace_id: string
  key: string
  name: string
  description?: string
  lead_id?: string
  icon?: string
  created_at: string
}

export interface IssueType {
  id: string
  name: string
  icon?: string
  color?: string
}

export interface IssueStatus {
  id: string
  name: string
  category: 'todo' | 'in_progress' | 'done'
  color?: string
  position: number
}

export interface IssuePriority {
  id: string
  name: string
  icon?: string
  color?: string
}

export interface Issue {
  id: string
  key: string
  title: string
  description?: string
  project_id: string
  sprint_id?: string
  issue_type_id: string
  issue_status_id: string
  issue_priority_id: string
  reporter_id: string
  assignee_id?: string
  story_points?: number
  due_date?: string
  created_at: string
  updated_at: string
  issue_type: IssueType
  issue_status: IssueStatus
  issue_priority: IssuePriority
  reporter: User
  assignee?: User
}

export interface Sprint {
  id: string
  project_id: string
  name: string
  goal?: string
  status: 'planning' | 'active' | 'completed' | 'closed'
  start_date?: string
  end_date?: string
}

export interface BoardColumn {
  id: string
  name: string
  issue_status_id?: string
  position: number
  issues: BoardColumnIssue[]
}

export interface BoardColumnIssue {
  id: string
  issue_id: string
  position: number
  issue: Issue
}

export interface Board {
  id: string
  project_id: string
  name: string
  board_type: 'kanban' | 'scrum'
  columns: BoardColumn[]
}

export interface WikiPage {
  id: string
  workspace_id: string
  title: string
  slug: string
  content: string
  parent_id?: string
  author_id: string
  is_published: boolean
  created_at: string
  updated_at: string
  author: User
}

export interface Room {
  id: string
  workspace_id: string
  project_id?: string
  issue_id?: string
  name?: string
  room_type: 'direct' | 'group' | 'project' | 'issue'
  created_at: string
}

export interface RoomCreate {
  name?: string
  room_type: 'direct' | 'group' | 'project' | 'issue'
  project_id?: string
  issue_id?: string
  member_ids: string[]
}

export interface RoomDetail extends Room {
  last_message?: MessageRead
  unread_count: number
}

export interface MessageRead {
  id: string
  room_id: string
  author_id: string
  content: string
  mentions?: Record<string, any>
  created_at: string
  author: User
}
