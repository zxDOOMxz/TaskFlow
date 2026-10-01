from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import Board, BoardColumn, IssueStatus, Project, ProjectMember, User, Workspace
from app.routers.workspaces import get_workspace_by_slug, is_workspace_admin
from app.schemas.projects import (
    ProjectCreate,
    ProjectDetail,
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectRead,
    ProjectUpdate,
)

router = APIRouter()


def get_project(workspace_slug: str, project_key: str, db: Session) -> Project:
    ws = get_workspace_by_slug(workspace_slug, db)
    project = db.query(Project).filter(Project.workspace_id == ws.id, Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("", response_model=List[ProjectRead])
def list_projects(workspace_slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    return db.query(Project).filter(Project.workspace_id == ws.id).all()


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    workspace_slug: str,
    data: ProjectCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    if not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Admin or manager required")

    existing = db.query(Project).filter(Project.workspace_id == ws.id, Project.key == data.key.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project key already exists")

    project = Project(
        workspace_id=ws.id,
        key=data.key.upper(),
        name=data.name,
        description=data.description,
        lead_id=user.id,
    )
    db.add(project)
    db.flush()

    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="admin"))
    db.flush()

    # Create default Kanban board
    board = Board(project_id=project.id, name="Board", board_type="kanban")
    db.add(board)
    db.flush()

    statuses = {s.name: s for s in db.query(IssueStatus).filter(IssueStatus.workspace_id == ws.id).all()}
    default_columns = [
        ("To Do", statuses.get("To Do")),
        ("In Progress", statuses.get("In Progress")),
        ("Review", statuses.get("Review")),
        ("Done", statuses.get("Done")),
    ]
    for idx, (name, status_obj) in enumerate(default_columns):
        col = BoardColumn(
            board_id=board.id,
            name=name,
            issue_status_id=status_obj.id if status_obj else None,
            position=idx,
        )
        db.add(col)

    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_key}", response_model=ProjectDetail)
def get_project_detail(
    workspace_slug: str,
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(workspace_slug, project_key, db)
    require_workspace_member(project.workspace, user)
    return project


@router.put("/{project_key}", response_model=ProjectRead)
def update_project(
    workspace_slug: str,
    project_key: str,
    data: ProjectUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(workspace_slug, project_key, db)
    member = next((m for m in project.members if m.user_id == user.id and m.role in ("admin", "manager")), None)
    if not member and not is_workspace_admin(project.workspace, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    if data.name:
        project.name = data.name
    if data.description is not None:
        project.description = data.description
    if data.lead_id:
        project.lead_id = data.lead_id
    if data.icon:
        project.icon = data.icon

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_key}")
def delete_project(
    workspace_slug: str,
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(workspace_slug, project_key, db)
    member = next((m for m in project.members if m.user_id == user.id and m.role == "admin"), None)
    if not member and not is_workspace_admin(project.workspace, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.get("/{project_key}/members", response_model=List[ProjectMemberRead])
def list_project_members(
    workspace_slug: str,
    project_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(workspace_slug, project_key, db)
    require_workspace_member(project.workspace, user)
    return project.members


@router.post("/{project_key}/members", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def add_project_member(
    workspace_slug: str,
    project_key: str,
    data: ProjectMemberCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(workspace_slug, project_key, db)
    member = next((m for m in project.members if m.user_id == user.id and m.role in ("admin", "manager")), None)
    if not member and not is_workspace_admin(project.workspace, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    target = db.query(User).filter(User.email == data.email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    ws_member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project.id, ProjectMember.user_id == target.id
    ).first()
    if ws_member:
        raise HTTPException(status_code=400, detail="User already in project")

    new_member = ProjectMember(project_id=project.id, user_id=target.id, role=data.role)
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    return new_member
