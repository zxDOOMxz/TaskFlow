from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import Issue, Project, Sprint
from app.routers.workspaces import is_workspace_admin
from app.schemas.sprints import (
    BurndownChart,
    BurndownPoint,
    SprintCreate,
    SprintDetail,
    SprintRead,
    SprintUpdate,
)

router = APIRouter()


def get_project(project_key: str, db: Session) -> Project:
    project = db.query(Project).filter(Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def can_manage_sprints(project: Project, user):
    if is_workspace_admin(project.workspace, user):
        return True
    member = next((m for m in project.members if m.user_id == user.id and m.role in ("admin", "manager")), None)
    return bool(member)


@router.get("", response_model=List[SprintRead])
def list_sprints(project_key: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)
    return db.query(Sprint).filter(Sprint.project_id == project.id).order_by(Sprint.created_at.desc()).all()


@router.post("", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
def create_sprint(
    project_key: str,
    data: SprintCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(project_key, db)
    if not can_manage_sprints(project, user):
        raise HTTPException(status_code=403, detail="Manager or admin required")

    sprint = Sprint(
        project_id=project.id,
        name=data.name,
        goal=data.goal,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("/{sprint_id}", response_model=SprintDetail)
def get_sprint(project_key: str, sprint_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)
    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return sprint


@router.put("/{sprint_id}", response_model=SprintRead)
def update_sprint(
    project_key: str,
    sprint_id: UUID,
    data: SprintUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = get_project(project_key, db)
    if not can_manage_sprints(project, user):
        raise HTTPException(status_code=403, detail="Manager or admin required")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(sprint, field, value)

    db.commit()
    db.refresh(sprint)
    return sprint


@router.post("/{sprint_id}/start", response_model=SprintRead)
def start_sprint(project_key: str, sprint_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    if not can_manage_sprints(project, user):
        raise HTTPException(status_code=403, detail="Manager or admin required")

    active = db.query(Sprint).filter(Sprint.project_id == project.id, Sprint.status == "active").first()
    if active:
        raise HTTPException(status_code=400, detail="Another sprint is active")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    sprint.status = "active"
    if not sprint.start_date:
        sprint.start_date = datetime.now(timezone.utc)
    if not sprint.end_date:
        sprint.end_date = sprint.start_date + timedelta(weeks=2)

    db.commit()
    db.refresh(sprint)
    return sprint


@router.post("/{sprint_id}/complete", response_model=SprintRead)
def complete_sprint(project_key: str, sprint_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    if not can_manage_sprints(project, user):
        raise HTTPException(status_code=403, detail="Manager or admin required")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    sprint.status = "completed"
    db.commit()
    db.refresh(sprint)
    return sprint


@router.post("/{sprint_id}/close", response_model=SprintRead)
def close_sprint(project_key: str, sprint_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    if not can_manage_sprints(project, user):
        raise HTTPException(status_code=403, detail="Manager or admin required")

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    for issue in sprint.issues:
        if issue.issue_status.category != "done":
            issue.sprint_id = None

    sprint.status = "closed"
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("/{sprint_id}/burndown", response_model=BurndownChart)
def burndown(project_key: str, sprint_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_project(project_key, db)
    require_workspace_member(project.workspace, user)

    sprint = db.query(Sprint).filter(Sprint.id == sprint_id, Sprint.project_id == project.id).first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")

    total = len(sprint.issues)
    if not sprint.start_date or not sprint.end_date or total == 0:
        return BurndownChart(sprint_id=sprint.id, points=[])

    start = sprint.start_date
    end = sprint.end_date
    days = (end - start).days or 1
    points = []

    for day in range(days + 1):
        date = (start + timedelta(days=day)).date().isoformat()
        done_count = sum(
            1
            for issue in sprint.issues
            if issue.issue_status.category == "done"
            and issue.updated_at.date() <= (start + timedelta(days=day)).date()
        )
        remaining = total - done_count
        points.append(BurndownPoint(date=date, remaining=max(0, remaining), total=total))

    return BurndownChart(sprint_id=sprint.id, points=points)
