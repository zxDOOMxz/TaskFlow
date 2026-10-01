import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { BoardColumn, Issue } from '@/types'
import { SortableIssueCard } from './IssueCard'

interface BoardColumnProps {
  column: BoardColumn
  onIssueClick: (issue: Issue) => void
}

export function BoardColumnView({ column, onIssueClick }: BoardColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id: column.id })

  const itemIds = column.issues.map((colIssue) => colIssue.id)

  return (
    <div
      ref={setNodeRef}
      className={`flex-shrink-0 w-80 rounded-xl p-3 flex flex-col max-h-full transition-colors ${
        isOver ? 'bg-primary-100' : 'bg-slate-100'
      }`}
    >
      <div className="flex items-center justify-between mb-3 px-1">
        <h3 className="font-semibold text-slate-700 text-sm">{column.name}</h3>
        <span className="text-xs text-slate-500 bg-slate-200 px-2 py-0.5 rounded-full">
          {column.issues.length}
        </span>
      </div>
      <SortableContext
        id={column.id}
        items={itemIds}
        strategy={verticalListSortingStrategy}
      >
        <div className="flex-1 overflow-y-auto space-y-2 min-h-[100px]">
          {column.issues.map((colIssue) => (
            <SortableIssueCard
              key={colIssue.id}
              id={colIssue.id}
              issue={colIssue.issue}
              onClick={() => onIssueClick(colIssue.issue)}
            />
          ))}
        </div>
      </SortableContext>
    </div>
  )
}
