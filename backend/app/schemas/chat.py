from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.workspaces import UserShort


class RoomBase(BaseModel):
    name: Optional[str] = None
    room_type: str = Field(default="group", pattern="^(direct|group|project|issue)$")


class RoomCreate(RoomBase):
    project_id: Optional[UUID] = None
    issue_id: Optional[UUID] = None
    member_ids: List[UUID] = []


class RoomRead(RoomBase):
    id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    issue_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RoomDetail(RoomRead):
    last_message: Optional["MessageRead"] = None
    unread_count: int = 0


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)


class MessageRead(MessageCreate):
    id: UUID
    room_id: UUID
    author_id: UUID
    mentions: Optional[dict] = None
    created_at: datetime
    author: UserShort

    class Config:
        from_attributes = True


RoomDetail.model_rebuild()
