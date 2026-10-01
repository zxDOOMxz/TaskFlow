from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.workspaces import UserShort


class ProjectMemberBase(BaseModel):
    user_id: UUID
    role: str = Field(..., pattern="^(admin|manager|developer|viewer)$")


class ProjectMemberCreate(BaseModel):
    email: str
    role: str = Field(default="developer", pattern="^(admin|manager|developer|viewer)$")


class ProjectMemberRead(ProjectMemberBase):
    id: UUID
    created_at: datetime
    user: UserShort

    class Config:
        from_attributes = True


class ProjectBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=10, pattern="^[A-Z][A-Z0-9]*$")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    lead_id: Optional[UUID] = None
    icon: Optional[str] = None


class ProjectRead(ProjectBase):
    id: UUID
    workspace_id: UUID
    lead_id: Optional[UUID] = None
    icon: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetail(ProjectRead):
    members: List[ProjectMemberRead] = []
    lead: Optional[UserShort] = None
