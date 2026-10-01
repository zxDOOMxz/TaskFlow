from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import (
    Board,
    BoardColumnIssue,
    Issue,
    IssueComment,
    IssueLink,
    IssuePriority,
    IssueStatus,
    IssueTimeLog,
    IssueType,
    Project,
    User,
)
from app.mentions import create_mention_notifications
from app.routers.workspaces import is_workspace_admin
from app.schemas.issues import (
    IssueCommentCreate,
    IssueCommentRead,
    IssueCreate,
    IssueDetail,
    IssueLinkCreate,
    IssueLinkRead,
    IssueRead,
    IssueTimeLogCreate,
    IssueTimeLogRead,
    IssueUpdate,
)

router = APIRouter()


def get_project_and_workspace(project_key: str, db: Session):
    project = db.query(Project).filter(Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def get_next_issue_key(project: Project, db: Session) -> str:
    last = (
        db.query(Issue)
        .filter(Issue.project_id == project.id)
        .order_by(Issue.created_at.desc())
        .first()
    )
    number = 1
    if last and last.key.startswith(f"{project.key}-"):
        try:
            number = int(last.key.split("-")[-1]) + 1
        except ValueError:
            number = 1
    return f"{project.key}-{number}"


def can_edit_issue(issue: Issue, user: User):
    if issue.reporter_id == user.id:
        return True
    if issue.assignee_id == user.id:
        return True
    if is_workspace_admin(issue.project.workspace, user):
        return True
    member = next((m for m in issue.project.members if m.user_id == user.id and m.role in ("admin", "manager")), None)
    return bool(member)


@router.get("", response_model=List[IssueRead])
def list_issues(
    project_key: str,
    sprint_id: Optional[UUID] = None,
    status_id: Optional[UUID] = None,
    assignee_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    require_workspace_member(project.workspace, user)

    query = db.query(Issue).filter(Issue.project_id == project.id)
    if sprint_id:
        query = query.filter(Issue.sprint_id == sprint_id)
    if status_id:
        query = query.filter(Issue.issue_status_id == status_id)
    if assignee_id:
        query = query.filter(Issue.assignee_id == assignee_id)

    return query.order_by(Issue.created_at.desc()).all()


@router.post("", response_model=IssueRead, status_code=status.HTTP_201_CREATED)
def create_issue(
    project_key: str,
    data: IssueCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    require_workspace_member(project.workspace, user)

    if data.issue_type_id:
        issue_type = db.query(IssueType).filter(IssueType.id == data.issue_type_id).first()
        if not issue_type or issue_type.workspace_id != project.workspace_id:
            raise HTTPException(status_code=400, detail="Invalid issue type")
    else:
        issue_type = db.query(IssueType).filter(IssueType.workspace_id == project.workspace_id).first()

    if data.issue_priority_id:
        priority = db.query(IssuePriority).filter(IssuePriority.id == data.issue_priority_id).first()
        if not priority or priority.workspace_id != project.workspace_id:
            raise HTTPException(status_code=400, detail="Invalid priority")
    else:
        priority = db.query(IssuePriority).filter(IssuePriority.workspace_id == project.workspace_id).first()

    default_status = (
        db.query(IssueStatus)
        .filter(IssueStatus.workspace_id == project.workspace_id, IssueStatus.category == "todo")
        .order_by(IssueStatus.position)
        .first()
    )

    issue = Issue(
        project_id=project.id,
        sprint_id=data.sprint_id,
        parent_id=data.parent_id,
        issue_type_id=issue_type.id if issue_type else data.issue_type_id,
        issue_status_id=default_status.id,
        issue_priority_id=priority.id if priority else data.issue_priority_id,
        reporter_id=user.id,
        assignee_id=data.assignee_id,
        key=get_next_issue_key(project, db),
        title=data.title,
        description=data.description,
        story_points=data.story_points,
        original_estimate_minutes=data.original_estimate_minutes,
        remaining_estimate_minutes=data.original_estimate_minutes,
        due_date=data.due_date,
    )
    db.add(issue)
    db.flush()

    # Add issue to all project boards in matching column
    boards = db.query(Board).filter(Board.project_id == project.id).all()
    for board in boards:
        for col in board.columns:
            if col.issue_status_id == default_status.id:
                position = (
                    db.query(BoardColumnIssue)
                    .filter(BoardColumnIssue.board_column_id == col.id)
                    .count()
                )
                db.add(BoardColumnIssue(board_column_id=col.id, issue_id=issue.id, position=position))
                break

    db.commit()
    db.refresh(issue)
    return issue


@router.get("/{issue_key}", response_model=IssueDetail)
def get_issue(
    project_key: str,
    issue_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    require_workspace_member(project.workspace, user)
    issue = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


@router.put("/{issue_key}", response_model=IssueRead)
def update_issue(
    project_key: str,
    issue_key: str,
    data: IssueUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    issue = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if not can_edit_issue(issue, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(issue, field, value)

    db.commit()
    db.refresh(issue)
    return issue


@router.delete("/{issue_key}")
def delete_issue(
    project_key: str,
    issue_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    issue = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if not can_edit_issue(issue, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(issue)
    db.commit()
    return {"message": "Issue deleted"}


@router.post("/{issue_key}/comments", response_model=IssueCommentRead, status_code=status.HTTP_201_CREATED)
async def add_comment(
    project_key: str,
    issue_key: str,
    data: IssueCommentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    require_workspace_member(project.workspace, user)
    issue = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    comment = IssueComment(issue_id=issue.id, author_id=user.id, content=data.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)

    create_mention_notifications(
        db,
        data.content,
        user,
        project.workspace_id,
        "issue",
        issue.id,
        issue.key,
    )

    return comment


@router.post("/{issue_key}/time-logs", response_model=IssueTimeLogRead, status_code=status.HTTP_201_CREATED)
def add_time_log(
    project_key: str,
    issue_key: str,
    data: IssueTimeLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    issue = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    time_log = IssueTimeLog(issue_id=issue.id, user_id=user.id, minutes=data.minutes, description=data.description)
    issue.logged_time_minutes = (issue.logged_time_minutes or 0) + data.minutes
    db.add(time_log)
    db.commit()
    db.refresh(time_log)
    return time_log


@router.post("/{issue_key}/links", response_model=IssueLinkRead, status_code=status.HTTP_201_CREATED)
def add_link(
    project_key: str,
    issue_key: str,
    data: IssueLinkCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project_and_workspace(project_key, db)
    source = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == issue_key.upper()).first()
    if not source:
        raise HTTPException(status_code=404, detail="Issue not found")

    target = db.query(Issue).filter(Issue.project_id == project.id, Issue.key == data.target_issue_key.upper()).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target issue not found")

    if source.id == target.id:
        raise HTTPException(status_code=400, detail="Cannot link issue to itself")

    link = IssueLink(source_issue_id=source.id, target_issue_id=target.id, link_type=data.link_type)
    db.add(link)
    db.commit()
    db.refresh(link)
    return IssueLinkRead(
        id=link.id,
        source_issue_id=link.source_issue_id,
        target_issue_id=link.target_issue_id,
        target_issue_key=target.key,
        target_issue_title=target.title,
        link_type=link.link_type,
    )
