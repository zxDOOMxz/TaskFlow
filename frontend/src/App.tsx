import { useEffect, useState } from 'react'
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
import { workspaceApi } from '@/api/workspaces'

function WorkspaceLayout() {
  const { workspaceSlug } = useParams()
  const { session } = useAuth()
  const { workspace, setWorkspace } = useAuthStore()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    if (!workspaceSlug || !session) {
      setLoading(false)
      return
    }
    if (workspace?.slug === workspaceSlug) {
      setLoading(false)
      return
    }
    setLoading(true)
    setError('')
    workspaceApi
      .get(workspaceSlug)
      .then(({ data }) => {
        if (!active) return
        setWorkspace(data)
      })
      .catch((err) => {
        if (!active) return
        console.error('Failed to load workspace:', err)
        setError('Рабочее пространство не найдено')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [workspaceSlug, session, workspace, setWorkspace])

  if (!session) return <Navigate to="/login" />
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  if (error || !workspace) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <p className="text-red-600 mb-2">{error || 'Рабочее пространство не загружено'}</p>
          <a href="/" className="text-primary-600 hover:underline">На главную</a>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar workspaceSlug={workspaceSlug!} />
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/projects/:projectKey" element={<ProjectBoardPage />} />
          <Route path="/projects/:projectKey/issues/:issueKey" element={<ProjectBoardPage />} />
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
  const navigate = useNavigate()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (loading) return
    if (!session) {
      setChecking(false)
      return
    }
    workspaceApi
      .list()
      .then(({ data }) => {
        if (data.length > 0) {
          navigate(`/w/${data[0].slug}`)
        } else {
          navigate('/workspaces/new')
        }
      })
      .catch((err) => {
        console.error('Failed to list workspaces:', err)
        setChecking(false)
      })
  }, [loading, session, navigate])

  if (loading || checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!session) return <Navigate to="/login" />
  return null
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
