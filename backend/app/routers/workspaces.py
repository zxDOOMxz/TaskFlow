from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import User, Workspace, WorkspaceMember
from app.schemas.workspaces import (
    WorkspaceCreate,
    WorkspaceDetail,
    WorkspaceMemberCreate,
    WorkspaceMemberRead,
    WorkspaceRead,
    WorkspaceUpdate,
)
from app.security import get_password_hash

router = APIRouter()


def is_workspace_admin(workspace: Workspace, user: User) -> bool:
    if workspace.owner_id == user.id:
        return True
    member = next((m for m in workspace.members if m.user_id == user.id and m.role == "admin"), None)
    return bool(member)


def get_workspace_by_slug(slug: str, db: Session) -> Workspace:
    ws = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


@router.get("", response_model=List[WorkspaceRead])
def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    owned = db.query(Workspace).filter(Workspace.owner_id == user.id).all()
    member_ws_ids = [m.workspace_id for m in user.workspaces]
    member_ws = db.query(Workspace).filter(Workspace.id.in_(member_ws_ids)).all() if member_ws_ids else []
    return list({ws.id: ws for ws in owned + member_ws}.values())


@router.post("", response_model=WorkspaceRead, status_code=status.HTTP_201_CREATED)
def create_workspace(data: WorkspaceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    import re

    slug = re.sub(r"[^a-z0-9-]", "-", data.name.lower()).strip("-")
    if not slug:
        slug = "workspace"
    base_slug = slug
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    workspace = Workspace(name=data.name, slug=slug, owner_id=user.id)
    db.add(workspace)
    db.flush()

    from app.routers.auth import create_default_workspace_data

    db.add_all(create_default_workspace_data(workspace.id))
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/{workspace_slug}", response_model=WorkspaceDetail)
def get_workspace(workspace_slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    return ws


@router.put("/{workspace_slug}", response_model=WorkspaceRead)
def update_workspace(
    workspace_slug: str,
    data: WorkspaceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    if not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Admin required")

    if data.name:
        ws.name = data.name
    if data.logo_url is not None:
        ws.logo_url = data.logo_url

    db.commit()
    db.refresh(ws)
    return ws


@router.delete("/{workspace_slug}")
def delete_workspace(workspace_slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    if ws.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only owner can delete workspace")
    db.delete(ws)
    db.commit()
    return {"message": "Workspace deleted"}


@router.get("/{workspace_slug}/members", response_model=List[WorkspaceMemberRead])
def list_members(workspace_slug: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    return ws.members


@router.post("/{workspace_slug}/members", response_model=WorkspaceMemberRead, status_code=status.HTTP_201_CREATED)
def add_member(
    workspace_slug: str,
    data: WorkspaceMemberCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    if not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Admin required")

    target = db.query(User).filter(User.email == data.email).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(WorkspaceMember).filter(
        WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == target.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already in workspace")

    member = WorkspaceMember(workspace_id=ws.id, user_id=target.id, role=data.role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.put("/{workspace_slug}/members/{member_id}", response_model=WorkspaceMemberRead)
def update_member(
    workspace_slug: str,
    member_id: UUID,
    data: WorkspaceMemberCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    if not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Admin required")

    member = db.query(WorkspaceMember).filter(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == ws.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = data.role
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{workspace_slug}/members/{member_id}")
def remove_member(
    workspace_slug: str,
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    if not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Admin required")

    member = db.query(WorkspaceMember).filter(WorkspaceMember.id == member_id, WorkspaceMember.workspace_id == ws.id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.user_id == ws.owner_id:
        raise HTTPException(status_code=400, detail="Cannot remove workspace owner")

    db.delete(member)
    db.commit()
    return {"message": "Member removed"}
