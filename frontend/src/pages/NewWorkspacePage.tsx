import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { workspaceApi } from '@/api/workspaces'

export function NewWorkspacePage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    setLoading(true)
    setError('')
    try {
      const { data } = await workspaceApi.create({ name: trimmed })
      navigate(`/w/${data.slug}`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Не удалось создать workspace')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        <h1 className="text-xl font-semibold text-slate-900 mb-2">Новое рабочее пространство</h1>
        <p className="text-sm text-slate-500 mb-6">
          Workspace — это место для проектов, задач, wiki и файлов вашей команды.
        </p>
        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Название"
            placeholder="Моя команда"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Создание...' : 'Создать'}
          </Button>
        </form>
      </div>
    </div>
  )
}
