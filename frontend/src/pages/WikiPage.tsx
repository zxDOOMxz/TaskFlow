import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { TopBar } from '@/components/layout/TopBar'
import api from '@/api/client'
import { WikiPage as WikiPageType } from '@/types'
import { MarkdownMention } from '@/components/common/MarkdownMention'

export function WikiPage() {
  const { workspaceSlug } = useParams()
  const [pages, setPages] = useState<WikiPageType[]>([])
  const [selectedPage, setSelectedPage] = useState<WikiPageType | null>(null)
  const [isEditorOpen, setIsEditorOpen] = useState(false)
  const [form, setForm] = useState({ title: '', content: '' })

  useEffect(() => {
    if (!workspaceSlug) return
    loadPages()
  }, [workspaceSlug])

  const loadPages = () => {
    api.get(`/workspaces/${workspaceSlug}/wiki/pages`).then((res) => {
      setPages(res.data)
    })
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    const title = form.title.trim()
    if (!title) return
    const payload = { title, content: form.content }
    if (selectedPage) {
      await api.put(`/workspaces/${workspaceSlug}/wiki/pages/${selectedPage.id}`, payload)
    } else {
      await api.post(`/workspaces/${workspaceSlug}/wiki/pages`, payload)
    }
    setIsEditorOpen(false)
    setSelectedPage(null)
    setForm({ title: '', content: '' })
    loadPages()
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title="Wiki">
        <Button onClick={() => { setSelectedPage(null); setForm({ title: '', content: '' }); setIsEditorOpen(true) }}>
          + Новая страница
        </Button>
      </TopBar>
      <div className="flex flex-1 overflow-hidden">
        <aside className="w-64 bg-white border-r border-slate-200 overflow-y-auto p-4">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Страницы</h3>
          {pages.length === 0 ? (
            <p className="text-sm text-slate-400">Нет страниц</p>
          ) : (
            <ul className="space-y-1">
              {pages.map((page) => (
                <li key={page.id}>
                  <button
                    onClick={() => setSelectedPage(page)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                      selectedPage?.id === page.id
                        ? 'bg-primary-50 text-primary-700 font-medium'
                        : 'text-slate-700 hover:bg-slate-100'
                    }`}
                  >
                    {page.title}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>
        <main className="flex-1 overflow-y-auto p-8 bg-white">
          {selectedPage ? (
            <div>
              <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-slate-900">{selectedPage.title}</h1>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setForm({ title: selectedPage.title, content: selectedPage.content })
                    setIsEditorOpen(true)
                  }}
                >
                  Редактировать
                </Button>
              </div>
              <div className="prose prose-slate max-w-none">
                <MarkdownMention text={selectedPage.content} workspaceSlug={workspaceSlug || ''} />
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <p className="text-slate-500 mb-4">Выберите страницу или создайте новую</p>
              <Button onClick={() => { setSelectedPage(null); setForm({ title: '', content: '' }); setIsEditorOpen(true) }}>
                Создать страницу
              </Button>
            </div>
          )}
        </main>
      </div>

      <Modal
        isOpen={isEditorOpen}
        onClose={() => setIsEditorOpen(false)}
        title={selectedPage ? 'Редактировать страницу' : 'Новая страница'}
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsEditorOpen(false)}>Отмена</Button>
            <Button type="submit" form="wiki-form">Сохранить</Button>
          </>
        }
      >
        <form id="wiki-form" onSubmit={handleSave} className="space-y-4">
          <Input
            label="Заголовок"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Содержимое (Markdown)</label>
            <textarea
              className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
              rows={10}
              value={form.content}
              onChange={(e) => setForm({ ...form, content: e.target.value })}
            />
          </div>
        </form>
      </Modal>
    </div>
  )
}
