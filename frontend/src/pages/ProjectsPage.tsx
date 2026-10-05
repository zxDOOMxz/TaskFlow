import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { TopBar } from '@/components/layout/TopBar'
import { useAuthStore } from '@/stores/authStore'
import { projectApi, workspaceApi } from '@/api/workspaces'
import { Project } from '@/types'

export function ProjectsPage() {
  const { workspace } = useAuthStore()
  const navigate = useNavigate()
  const [projects, setProjects] = useState<Project[]>([])
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form, setForm] = useState({ key: '', name: '', description: '' })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!workspace) return
    loadProjects()
  }, [workspace])

  const loadProjects = () => {
    workspaceApi.projects(workspace!.slug).then((res) => setProjects(res.data))
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!workspace) return
    const key = form.key.trim().toUpperCase()
    const name = form.name.trim()
    if (!key || !name) return
    setLoading(true)
    try {
      await projectApi.create(workspace.slug, {
        key,
        name,
        description: form.description,
      })
      setIsModalOpen(false)
      setForm({ key: '', name: '', description: '' })
      loadProjects()
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="Проекты">
        <Button onClick={() => setIsModalOpen(true)}>+ Новый проект</Button>
      </TopBar>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-5xl mx-auto">
          {projects.length === 0 ? (
            <div className="card p-12 text-center">
              <h3 className="text-lg font-medium text-slate-900 mb-2">Нет проектов</h3>
              <p className="text-slate-500 mb-4">Создайте первый проект, чтобы начать работу</p>
              <Button onClick={() => setIsModalOpen(true)}>Создать проект</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((project) => (
                <div
                  key={project.id}
                  onClick={() => navigate(`/w/${workspace?.slug}/projects/${project.key}`)}
                  className="card p-5 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 text-primary-700 flex items-center justify-center font-bold text-sm">
                      {project.key}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-slate-900 truncate">{project.name}</h3>
                      <p className="text-xs text-slate-500 font-mono">{project.key}</p>
                    </div>
                  </div>
                  <p className="text-sm text-slate-500 line-clamp-2">
                    {project.description || 'Нет описания'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Новый проект"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Отмена</Button>
            <Button type="submit" form="project-form" disabled={loading}>
              {loading ? 'Создание...' : 'Создать'}
            </Button>
          </>
        }
      >
        <form id="project-form" onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Ключ проекта"
            placeholder="TF"
            value={form.key}
            onChange={(e) => setForm({ ...form, key: e.target.value })}
            required
          />
          <Input
            label="Название"
            placeholder="TaskFlow"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            required
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Описание</label>
            <textarea
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  )
}
