from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import File as FileModel, Project, User, Workspace
from app.routers.workspaces import get_workspace_by_slug
from app.schemas.workspaces import UserShort
from app.storage import delete_file, get_presigned_url, upload_file

router = APIRouter()


class FileRead:
    pass


from pydantic import BaseModel


class FileReadSchema(BaseModel):
    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID]
    uploaded_by_id: UUID
    original_name: str
    storage_key: str
    mime_type: str
    size_bytes: int
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    created_at: datetime
    url: Optional[str] = None
    uploaded_by: UserShort

    class Config:
        from_attributes = True


@router.get("", response_model=List[FileReadSchema])
def list_files(
    workspace_slug: str,
    project_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    query = db.query(FileModel).filter(FileModel.workspace_id == ws.id)
    if project_id:
        query = query.filter(FileModel.project_id == str(project_id))
    files = query.order_by(FileModel.created_at.desc()).all()

    result = []
    for f in files:
        data = FileReadSchema.model_validate(f)
        data.url = get_presigned_url(f.storage_key)
        result.append(data)
    return result


@router.post("/upload", response_model=FileReadSchema, status_code=status.HTTP_201_CREATED)
async def upload_file_endpoint(
    workspace_slug: str,
    file: UploadFile = File(...),
    project_id: Optional[UUID] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)

    if project_id:
        project = db.query(Project).filter(Project.id == str(project_id), Project.workspace_id == ws.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large (max {get_settings().max_upload_mb} MB)",
        )

    storage_key = upload_file(
        file_data=content,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        entity_type=entity_type,
    )

    db_file = FileModel(
        workspace_id=ws.id,
        project_id=str(project_id) if project_id else None,
        uploaded_by_id=user.id,
        original_name=file.filename or "unnamed",
        storage_key=storage_key,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    result = FileReadSchema.model_validate(db_file)
    result.url = get_presigned_url(db_file.storage_key)
    return result


@router.get("/{file_id}", response_model=FileReadSchema)
def get_file(
    workspace_slug: str,
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    f = db.query(FileModel).filter(FileModel.id == str(file_id), FileModel.workspace_id == ws.id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    result = FileReadSchema.model_validate(f)
    result.url = get_presigned_url(f.storage_key)
    return result


@router.delete("/{file_id}")
def delete_file_endpoint(
    workspace_slug: str,
    file_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    f = db.query(FileModel).filter(FileModel.id == str(file_id), FileModel.workspace_id == ws.id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if f.uploaded_by_id != user.id and not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    try:
        delete_file(f.storage_key)
    except Exception:
        pass

    db.delete(f)
    db.commit()
    return {"message": "File deleted"}


def is_workspace_admin(workspace: Workspace, user: User) -> bool:
    if workspace.owner_id == user.id:
        return True
    member = next((m for m in workspace.members if m.user_id == user.id and m.role == "admin"), None)
    return bool(member)
