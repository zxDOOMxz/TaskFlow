import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { useAuthStore } from '@/stores/authStore'
import { workspaceApi } from '@/api/workspaces'
import { Project } from '@/types'

export function DashboardPage() {
  const { workspace } = useAuthStore()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!workspace) return
    workspaceApi.projects(workspace.slug)
      .then((res) => setProjects(res.data))
      .finally(() => setLoading(false))
  }, [workspace])

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="Дашборд" />
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card p-5">
              <p className="text-sm text-slate-500 mb-1">Проекты</p>
              <p className="text-3xl font-bold text-slate-900">{projects.length}</p>
            </div>
            <div className="card p-5">
              <p className="text-sm text-slate-500 mb-1">Мои задачи</p>
              <p className="text-3xl font-bold text-slate-900">—</p>
            </div>
            <div className="card p-5">
              <p className="text-sm text-slate-500 mb-1">Wiki-страницы</p>
              <p className="text-3xl font-bold text-slate-900">—</p>
            </div>
          </div>

          <div className="card p-6">
            <h2 className="text-lg font-semibold mb-4">Проекты</h2>
            {loading ? (
              <p className="text-slate-500">Загрузка...</p>
            ) : projects.length === 0 ? (
              <p className="text-slate-500">Пока нет проектов. Создайте первый проект.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {projects.map((project) => (
                  <Link
                    key={project.id}
                    to={`/w/${workspace?.slug}/projects/${project.key}`}
                    className="block p-4 border border-slate-200 rounded-lg hover:border-primary-300 hover:shadow-sm transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold">
                        {project.key}
                      </div>
                      <div>
                        <h3 className="font-medium text-slate-900">{project.name}</h3>
                        <p className="text-sm text-slate-500">{project.description || 'Нет описания'}</p>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
