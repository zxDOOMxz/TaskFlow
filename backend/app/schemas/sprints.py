from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.issues import IssueRead


class SprintBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintCreate(SprintBase):
    pass


class SprintUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    goal: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SprintRead(SprintBase):
    id: UUID
    project_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SprintDetail(SprintRead):
    issues: List[IssueRead] = []


class BurndownPoint(BaseModel):
    date: str
    remaining: int
    total: int


class BurndownChart(BaseModel):
    sprint_id: UUID
    points: List[BurndownPoint]
