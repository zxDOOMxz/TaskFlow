from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.workspaces import UserShort


class IssueTypeRead(BaseModel):
    id: UUID
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class IssueStatusRead(BaseModel):
    id: UUID
    name: str
    category: str
    color: Optional[str] = None
    position: int

    class Config:
        from_attributes = True


class IssuePriorityRead(BaseModel):
    id: UUID
    name: str
    icon: Optional[str] = None
    color: Optional[str] = None

    class Config:
        from_attributes = True


class IssueCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class IssueCommentRead(IssueCommentCreate):
    id: UUID
    author_id: UUID
    author: UserShort
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IssueTimeLogCreate(BaseModel):
    minutes: int = Field(..., gt=0)
    description: Optional[str] = None


class IssueTimeLogRead(IssueTimeLogCreate):
    id: UUID
    user_id: UUID
    user: UserShort
    logged_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class IssueLinkCreate(BaseModel):
    target_issue_key: str
    link_type: str = Field(..., pattern="^(blocks|depends_on|duplicates|relates_to)$")


class IssueLinkRead(BaseModel):
    id: UUID
    source_issue_id: UUID
    target_issue_id: UUID
    target_issue_key: str
    target_issue_title: str
    link_type: str

    class Config:
        from_attributes = True


class IssueBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class IssueCreate(IssueBase):
    issue_type_id: Optional[UUID] = None
    issue_priority_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    sprint_id: Optional[UUID] = None
    story_points: Optional[int] = None
    original_estimate_minutes: Optional[int] = None
    due_date: Optional[datetime] = None


class IssueUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    issue_status_id: Optional[UUID] = None
    issue_priority_id: Optional[UUID] = None
    assignee_id: Optional[UUID] = None
    sprint_id: Optional[UUID] = None
    story_points: Optional[int] = None
    original_estimate_minutes: Optional[int] = None
    remaining_estimate_minutes: Optional[int] = None
    due_date: Optional[datetime] = None


class IssueRead(IssueBase):
    id: UUID
    key: str
    project_id: UUID
    sprint_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None
    issue_type_id: UUID
    issue_status_id: UUID
    issue_priority_id: UUID
    reporter_id: UUID
    assignee_id: Optional[UUID] = None
    story_points: Optional[int] = None
    original_estimate_minutes: Optional[int] = None
    remaining_estimate_minutes: Optional[int] = None
    logged_time_minutes: int
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    issue_type: IssueTypeRead
    issue_status: IssueStatusRead
    issue_priority: IssuePriorityRead
    reporter: UserShort
    assignee: Optional[UserShort] = None

    class Config:
        from_attributes = True


class IssueDetail(IssueRead):
    comments: List[IssueCommentRead] = []
    time_logs: List[IssueTimeLogRead] = []
    links: List[IssueLinkRead] = []
    subtasks: List[IssueRead] = []


class SprintShort(BaseModel):
    id: UUID
    name: str
    status: str

    class Config:
        from_attributes = True
