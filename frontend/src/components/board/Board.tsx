import { useState } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  MouseSensor,
  TouchSensor,
  closestCorners,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import { arrayMove } from '@dnd-kit/sortable'
import { Board, BoardColumn as BoardColumnType, Issue } from '@/types'
import { BoardColumnView } from './BoardColumn'
import { IssueCard } from './IssueCard'
import api from '@/api/client'

interface BoardProps {
  board: Board
  projectKey: string
  onIssueClick: (issue: Issue) => void
  onBoardUpdate?: (board: Board) => void
}

export function BoardView({ board, projectKey, onIssueClick, onBoardUpdate }: BoardProps) {
  const [columns, setColumns] = useState<BoardColumnType[]>(board.columns)
  const [activeIssue, setActiveIssue] = useState<Issue | null>(null)

  const sensors = useSensors(
    useSensor(MouseSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 250, tolerance: 5 } })
  )

  const handleDragStart = (event: DragStartEvent) => {
    const { active } = event
    const activeCol = columns.find((col) =>
      col.issues.some((item) => item.id === active.id)
    )
    if (activeCol) {
      const item = activeCol.issues.find((item) => item.id === active.id)
      if (item) {
        setActiveIssue(item.issue)
      }
    }
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event
    setActiveIssue(null)

    if (!over) return

    const activeId = active.id as string
    const overId = over.id as string

    const sourceColumn = columns.find((col) =>
      col.issues.some((item) => item.id === activeId)
    )
    if (!sourceColumn) return

    const sourceItem = sourceColumn.issues.find((item) => item.id === activeId)
    if (!sourceItem) return

    // Find target column: either dropped on a column or on an item in a column
    let targetColumn = columns.find((col) => col.id === overId)
    let targetIndex = -1

    if (!targetColumn) {
      // Dropped on an item
      for (const col of columns) {
        const idx = col.issues.findIndex((item) => item.id === overId)
        if (idx !== -1) {
          targetColumn = col
          targetIndex = idx
          break
        }
      }
    }

    if (!targetColumn) return

    if (sourceColumn.id === targetColumn.id) {
      // Reorder within same column
      const oldIndex = sourceColumn.issues.findIndex((item) => item.id === activeId)
      const newIndex = targetIndex !== -1 ? targetIndex : sourceColumn.issues.findIndex((item) => item.id === overId)
      if (oldIndex === newIndex || newIndex === -1) return

      const newIssues = arrayMove(sourceColumn.issues, oldIndex, newIndex)
      updateColumnIssues(sourceColumn.id, newIssues)

      await moveIssueOnServer(
        projectKey,
        board.id,
        sourceItem.issue_id,
        sourceColumn.id,
        targetColumn.id,
        newIndex
      )
    } else {
      // Move between columns
      const newSourceIssues = sourceColumn.issues.filter((item) => item.id !== activeId)
      let newTargetIssues = [...targetColumn.issues]

      if (targetIndex !== -1) {
        newTargetIssues.splice(targetIndex, 0, sourceItem)
      } else {
        newTargetIssues.push(sourceItem)
      }

      const newColumns = columns.map((col) => {
        if (col.id === sourceColumn.id) return { ...col, issues: newSourceIssues }
        if (col.id === targetColumn.id) return { ...col, issues: newTargetIssues }
        return col
      })

      setColumns(newColumns)
      if (onBoardUpdate) {
        onBoardUpdate({ ...board, columns: newColumns })
      }

      await moveIssueOnServer(
        projectKey,
        board.id,
        sourceItem.issue_id,
        sourceColumn.id,
        targetColumn.id,
        targetIndex !== -1 ? targetIndex : newTargetIssues.length - 1
      )
    }
  }

  const updateColumnIssues = (columnId: string, newIssues: BoardColumnType['issues']) => {
    const newColumns = columns.map((col) =>
      col.id === columnId ? { ...col, issues: newIssues } : col
    )
    setColumns(newColumns)
    if (onBoardUpdate) {
      onBoardUpdate({ ...board, columns: newColumns })
    }
  }

  const moveIssueOnServer = async (
    projectKey: string,
    boardId: string,
    issueId: string,
    sourceColumnId: string,
    targetColumnId: string,
    newPosition: number
  ) => {
    try {
      await api.post(`/projects/${projectKey}/boards/${boardId}/issues/move`, {
        issue_id: issueId,
        source_column_id: sourceColumnId,
        target_column_id: targetColumnId,
        new_position: newPosition,
      })
    } catch (error) {
      console.error('Failed to move issue:', error)
      // Optionally revert or reload board
    }
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4 h-full">
        {columns.map((column) => (
          <BoardColumnView
            key={column.id}
            column={column}
            onIssueClick={onIssueClick}
          />
        ))}
      </div>
      <DragOverlay>
        {activeIssue ? (
          <div className="rotate-2">
            <IssueCard issue={activeIssue} />
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
