from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceMemberBase(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern="^(admin|manager|developer|viewer)$")


class WorkspaceMemberCreate(BaseModel):
    email: str
    role: str = Field(default="developer", pattern="^(admin|manager|developer|viewer)$")


class WorkspaceMemberRead(WorkspaceMemberBase):
    id: UUID
    created_at: datetime
    user: "UserShort"

    class Config:
        from_attributes = True


class WorkspaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class WorkspaceCreate(WorkspaceBase):
    pass


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    logo_url: Optional[str] = None


class WorkspaceRead(WorkspaceBase):
    id: UUID
    slug: str
    logo_url: Optional[str] = None
    owner_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceDetail(WorkspaceRead):
    members: List[WorkspaceMemberRead] = []


class UserShort(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


WorkspaceMemberRead.model_rebuild()
