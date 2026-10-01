import { useEffect } from 'react'
import { Navigate, Route, Routes, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import ProtectedRoute from '@/components/ProtectedRoute'
import { Sidebar } from '@/components/layout/Sidebar'
import { useAuthStore } from '@/stores/authStore'
import { DashboardPage } from '@/pages/DashboardPage'
import { LoginPage } from '@/pages/LoginPage'
import { ProjectsPage } from '@/pages/ProjectsPage'
import { ProjectBoardPage } from '@/pages/ProjectBoardPage'
import { WikiPage } from '@/pages/WikiPage'
import { ChatPage } from '@/pages/ChatPage'
import { FilesPage } from '@/pages/FilesPage'

function WorkspaceLayout() {
  const { workspaceSlug } = useParams()
  const { session } = useAuth()
  const { workspace, setWorkspace } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (!session) return
    if (workspace?.slug === workspaceSlug) return
    // TODO: load workspace via API once backend migration is complete
    setWorkspace({ id: workspaceSlug!, slug: workspaceSlug!, name: workspaceSlug! })
  }, [workspaceSlug, session, workspace, setWorkspace, navigate])

  if (!session) return <Navigate to="/login" />

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar workspaceSlug={workspaceSlug!} />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectKey" element={<ProjectBoardPage />} />
          <Route path="/wiki/*" element={<WikiPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/files" element={<FilesPage />} />
        </Routes>
      </main>
    </div>
  )
}

function RootRedirect() {
  const { session, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!session) return <Navigate to="/login" />
  return <Navigate to="/w/default" />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/w/:workspaceSlug/*"
        element={
          <ProtectedRoute>
            <WorkspaceLayout />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<RootRedirect />} />
    </Routes>
  )
}

export default App
