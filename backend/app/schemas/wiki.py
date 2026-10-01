from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.workspaces import UserShort


class WikiPageBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = ""


class WikiPageCreate(WikiPageBase):
    parent_id: Optional[UUID] = None
    slug: Optional[str] = None


class WikiPageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    parent_id: Optional[UUID] = None
    is_published: Optional[bool] = None


class WikiPageRead(WikiPageBase):
    id: UUID
    workspace_id: UUID
    parent_id: Optional[UUID] = None
    author_id: UUID
    slug: str
    position: int
    is_published: bool
    created_at: datetime
    updated_at: datetime
    author: UserShort

    class Config:
        from_attributes = True


class WikiPageTreeItem(WikiPageRead):
    children: List["WikiPageTreeItem"] = []


WikiPageTreeItem.model_rebuild()


class WikiPageVersionRead(BaseModel):
    id: UUID
    page_id: UUID
    author_id: UUID
    content: str
    version_number: int
    comment: Optional[str] = None
    created_at: datetime
    author: UserShort

    class Config:
        from_attributes = True
