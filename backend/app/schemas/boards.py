from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.issues import IssueRead


class BoardColumnIssueRead(BaseModel):
    id: UUID
    issue_id: UUID
    position: int
    issue: IssueRead

    class Config:
        from_attributes = True


class BoardColumnCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    issue_status_id: Optional[UUID] = None
    wip_limit: Optional[int] = Field(None, ge=0)
    position: int = 0


class BoardColumnRead(BoardColumnCreate):
    id: UUID
    issues: List[BoardColumnIssueRead] = []

    class Config:
        from_attributes = True


class BoardBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    board_type: str = Field(default="kanban", pattern="^(kanban|scrum)$")


class BoardCreate(BoardBase):
    columns: List[BoardColumnCreate] = []


class BoardRead(BoardBase):
    id: UUID
    project_id: UUID
    filter_query: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BoardDetail(BoardRead):
    columns: List[BoardColumnRead] = []


class IssueMoveRequest(BaseModel):
    issue_id: UUID
    source_column_id: UUID
    target_column_id: UUID
    new_position: int = 0
