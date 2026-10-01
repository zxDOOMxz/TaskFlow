import asyncio
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import Board, BoardColumn, BoardColumnIssue, Issue, IssueStatus, Project
from app.schemas.boards import (
    BoardColumnCreate,
    BoardCreate,
    BoardDetail,
    BoardRead,
    IssueMoveRequest,
)
from app.websocket import broadcast_event

router = APIRouter()


def get_project(project_key: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=List[BoardRead])
def list_boards(project_key: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)
    return db.query(Board).filter(Board.project_id == project.id).all()


@router.post("", response_model=BoardDetail, status_code=status.HTTP_201_CREATED)
def create_board(
    project_key: str,
    data: BoardCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)

    board = Board(project_id=project.id, name=data.name, board_type=data.board_type)
    db.add(board)
    db.flush()

    statuses = {s.name: s.id for s in db.query(IssueStatus).filter(IssueStatus.workspace_id == project.workspace_id).all()}

    default_columns = [
        ("To Do", "todo"),
        ("In Progress", "in_progress"),
        ("Review", "in_progress"),
        ("Done", "done"),
    ]

    created_columns = []

    if not data.columns:
        for idx, (name, category) in enumerate(default_columns):
            status_id = statuses.get(name)
            col = BoardColumn(board_id=board.id, name=name, issue_status_id=status_id, position=idx)
            db.add(col)
            created_columns.append(col)
    else:
        for idx, col_data in enumerate(data.columns):
            col = BoardColumn(
                board_id=board.id,
                name=col_data.name,
                issue_status_id=col_data.issue_status_id,
                position=idx if col_data.position is None else col_data.position,
                wip_limit=col_data.wip_limit,
            )
            db.add(col)
            created_columns.append(col)

    db.flush()

    # Populate board with existing issues matching column statuses
    for col in created_columns:
        if col.issue_status_id:
            issues = (
                db.query(Issue)
                .filter(Issue.project_id == project.id, Issue.issue_status_id == col.issue_status_id)
                .all()
            )
            for idx, issue in enumerate(issues):
                db.add(BoardColumnIssue(board_column_id=col.id, issue_id=issue.id, position=idx))

    db.commit()
    db.refresh(board)
    return board


@router.get("/{board_id}", response_model=BoardDetail)
def get_board(
    project_key: str,
    board_id: UUID,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)
    board = db.query(Board).filter(Board.id == board_id, Board.project_id == project.id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")
    return board


@router.post("/{board_id}/issues/move")
async def move_issue(
    project_key: str,
    board_id: UUID,
    data: IssueMoveRequest,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)

    board = db.query(Board).filter(Board.id == board_id, Board.project_id == project.id).first()
    if not board:
        raise HTTPException(status_code=404, detail="Board not found")

    source_col = db.query(BoardColumn).filter(BoardColumn.id == data.source_column_id, BoardColumn.board_id == board.id).first()
    target_col = db.query(BoardColumn).filter(BoardColumn.id == data.target_column_id, BoardColumn.board_id == board.id).first()

    if not source_col or not target_col:
        raise HTTPException(status_code=404, detail="Column not found")

    bci = (
        db.query(BoardColumnIssue)
        .filter(BoardColumnIssue.board_column_id == source_col.id, BoardColumnIssue.issue_id == data.issue_id)
        .first()
    )
    if not bci:
        raise HTTPException(status_code=404, detail="Issue not on source column")

    issue = db.query(Issue).filter(Issue.id == data.issue_id, Issue.project_id == project.id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    bci.board_column_id = target_col.id
    bci.position = data.new_position

    if target_col.issue_status_id:
        issue.issue_status_id = target_col.issue_status_id

    # Reorder target column issues
    target_issues = (
        db.query(BoardColumnIssue)
        .filter(BoardColumnIssue.board_column_id == target_col.id, BoardColumnIssue.id != bci.id)
        .order_by(BoardColumnIssue.position)
        .all()
    )
    for idx, item in enumerate(target_issues):
        if idx >= data.new_position:
            item.position = idx + 1
        else:
            item.position = idx

    db.commit()

    asyncio.create_task(
        broadcast_event(
            f"project:{project.id}",
            "issue_moved",
            {
                "issue_id": str(data.issue_id),
                "source_column_id": str(data.source_column_id),
                "target_column_id": str(data.target_column_id),
                "new_position": data.new_position,
                "issue_status_id": str(target_col.issue_status_id) if target_col.issue_status_id else None,
            },
        )
    )

    return {"message": "Issue moved"}
