import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Modal } from '@/components/ui/Modal'
import { TopBar } from '@/components/layout/TopBar'
import { BoardView } from '@/components/board/Board'
import { issueApi, projectApi } from '@/api/workspaces'
import { useWebSocket } from '@/hooks/useWebSocket'
import { MarkdownMention } from '@/components/common/MarkdownMention'
import { Board, Issue } from '@/types'

export function ProjectBoardPage() {
  const { workspaceSlug, projectKey } = useParams()
  const [board, setBoard] = useState<Board | null>(null)
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null)
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [form, setForm] = useState({
    title: '',
    description: '',
  })

  useEffect(() => {
    if (!projectKey) return
    loadBoard()
  }, [projectKey])

  const loadBoard = async () => {
    if (!projectKey) return
    const boardsRes = await projectApi.boards(projectKey)
    setBoard(boardsRes.data[0] || null)
  }

  const token = localStorage.getItem('access_token') || ''
  useWebSocket({
    roomId: board ? `project:${board.project_id}` : '',
    token,
    onMessage: (data) => {
      if (data.type === 'issue_moved') {
        loadBoard()
      }
    },
  })

  const handleCreateIssue = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!projectKey) return
    await issueApi.create(projectKey, form)
    setIsCreateOpen(false)
    setForm({ title: '', description: '' })
    loadBoard()
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <TopBar title={projectKey || 'Проект'}>
        <Button onClick={() => setIsCreateOpen(true)}>+ Создать задачу</Button>
      </TopBar>
      <div className="flex-1 overflow-hidden p-4 bg-slate-50">
        {board && projectKey ? (
          <BoardView
            board={board}
            projectKey={projectKey}
            onIssueClick={setSelectedIssue}
            onBoardUpdate={setBoard}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <p className="text-slate-500 mb-4">Доска ещё не создана</p>
              <Button onClick={() => setIsCreateOpen(true)}>Создать первую задачу</Button>
            </div>
          </div>
        )}
      </div>

      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Новая задача"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsCreateOpen(false)}>Отмена</Button>
            <Button onClick={handleCreateIssue}>Создать</Button>
          </>
        }
      >
        <form onSubmit={handleCreateIssue} className="space-y-4">
          <Input
            label="Название"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
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

      {selectedIssue && (
        <Modal
          isOpen={!!selectedIssue}
          onClose={() => setSelectedIssue(null)}
          title={`${selectedIssue.key}: ${selectedIssue.title}`}
          footer={
            <Button variant="secondary" onClick={() => setSelectedIssue(null)}>Закрыть</Button>
          }
        >
          <div className="space-y-3">
            <p className="text-sm text-slate-500">Тип: {selectedIssue.issue_type.name}</p>
            <p className="text-sm text-slate-500">Приоритет: {selectedIssue.issue_priority.name}</p>
            <p className="text-sm text-slate-500">Статус: {selectedIssue.issue_status.name}</p>
            <div className="text-sm text-slate-700">
              <MarkdownMention text={selectedIssue.description || 'Нет описания'} workspaceSlug={workspaceSlug || ''} />
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
