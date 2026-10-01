import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Issue } from '@/types'
import { Badge } from '@/components/ui/Badge'

interface IssueCardProps {
  issue: Issue
  onClick?: () => void
}

export function IssueCard({ issue, onClick }: IssueCardProps) {
  return (
    <div
      onClick={onClick}
      className="bg-white p-3 rounded-lg border border-slate-200 shadow-sm hover:shadow-md hover:border-primary-300 cursor-pointer transition-all group"
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <Badge color={issue.issue_type.color}>{issue.issue_type.name}</Badge>
        <Badge color={issue.issue_priority.color}>{issue.issue_priority.name}</Badge>
      </div>
      <h4 className="text-sm font-medium text-slate-900 mb-2 line-clamp-2 group-hover:text-primary-700">
        {issue.title}
      </h4>
      <div className="flex items-center justify-between text-xs text-slate-500">
        <span className="font-mono">{issue.key}</span>
        {issue.assignee ? (
          <div className="w-6 h-6 rounded-full bg-primary-100 text-primary-700 flex items-center justify-center font-medium">
            {issue.assignee.first_name[0]}
          </div>
        ) : (
          <div className="w-6 h-6 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center">
            ?
          </div>
        )}
      </div>
      {issue.story_points !== undefined && issue.story_points !== null && (
        <div className="mt-2 flex justify-end">
          <span className="text-xs bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
            {issue.story_points} SP
          </span>
        </div>
      )}
    </div>
  )
}

interface SortableIssueCardProps extends IssueCardProps {
  id: string
}

export function SortableIssueCard({ id, issue, onClick }: SortableIssueCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <IssueCard issue={issue} onClick={onClick} />
    </div>
  )
}
