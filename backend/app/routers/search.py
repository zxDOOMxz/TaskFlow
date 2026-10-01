from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import Issue, Project, User, WikiPage, Workspace
from app.routers.workspaces import get_workspace_by_slug

router = APIRouter()


class SearchResult:
    def __init__(self, id, type, title, subtitle, url):
        self.id = id
        self.type = type
        self.title = title
        self.subtitle = subtitle
        self.url = url


@router.get("")
def search(
    q: str,
    workspace_slug: str,
    type_filter: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)

    query = q.strip()
    if len(query) < 2:
        return []

    results = []
    like = f"%{query}%"

    if not type_filter or type_filter == "issue":
        issues = (
            db.query(Issue)
            .join(Project)
            .filter(
                Project.workspace_id == ws.id,
                or_(Issue.title.ilike(like), Issue.key.ilike(like), Issue.description.ilike(like)),
            )
            .limit(20)
            .all()
        )
        for issue in issues:
            results.append({
                "id": str(issue.id),
                "type": "issue",
                "title": issue.title,
                "subtitle": issue.key,
                "url": f"/projects/{issue.project.key}/issues/{issue.key}",
            })

    if not type_filter or type_filter == "page":
        pages = (
            db.query(WikiPage)
            .filter(
                WikiPage.workspace_id == ws.id,
                or_(WikiPage.title.ilike(like), WikiPage.content.ilike(like)),
            )
            .limit(20)
            .all()
        )
        for page in pages:
            results.append({
                "id": str(page.id),
                "type": "page",
                "title": page.title,
                "subtitle": "Wiki",
                "url": f"/wiki/{page.id}",
            })

    return results
