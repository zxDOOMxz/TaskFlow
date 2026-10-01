import re
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import User, WikiPage, WikiPageVersion, Workspace
from app.routers.workspaces import get_workspace_by_slug, is_workspace_admin
from app.schemas.wiki import WikiPageCreate, WikiPageRead, WikiPageTreeItem, WikiPageUpdate, WikiPageVersionRead

router = APIRouter()


def generate_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", title.lower()).strip("-")
    return slug or "page"


@router.get("/pages", response_model=List[WikiPageRead])
def list_pages(workspace_slug: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    return db.query(WikiPage).filter(WikiPage.workspace_id == ws.id, WikiPage.parent_id.is_(None)).order_by(WikiPage.position).all()


@router.get("/pages/tree", response_model=List[WikiPageTreeItem])
def get_page_tree(workspace_slug: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    pages = db.query(WikiPage).filter(WikiPage.workspace_id == ws.id).order_by(WikiPage.position).all()
    page_map = {p.id: WikiPageTreeItem.model_validate(p) for p in pages}
    roots = []
    for page in pages:
        item = page_map[page.id]
        if page.parent_id and page.parent_id in page_map:
            page_map[page.parent_id].children.append(item)
        else:
            roots.append(item)
    return roots


@router.post("/pages", response_model=WikiPageRead, status_code=status.HTTP_201_CREATED)
def create_page(
    workspace_slug: str,
    data: WikiPageCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)

    slug = data.slug or generate_slug(data.title)
    base_slug = slug
    counter = 1
    while db.query(WikiPage).filter(WikiPage.workspace_id == ws.id, WikiPage.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    page = WikiPage(
        workspace_id=ws.id,
        parent_id=data.parent_id,
        author_id=user.id,
        title=data.title,
        slug=slug,
        content=data.content,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.get("/pages/{page_id}", response_model=WikiPageRead)
def get_page(workspace_slug: str, page_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    page = db.query(WikiPage).filter(WikiPage.id == page_id, WikiPage.workspace_id == ws.id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page


@router.put("/pages/{page_id}", response_model=WikiPageRead)
def update_page(
    workspace_slug: str,
    page_id: UUID,
    data: WikiPageUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    page = db.query(WikiPage).filter(WikiPage.id == page_id, WikiPage.workspace_id == ws.id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.author_id != user.id and not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    # Save version
    versions_count = db.query(WikiPageVersion).filter(WikiPageVersion.page_id == page.id).count()
    version = WikiPageVersion(
        page_id=page.id,
        author_id=user.id,
        content=page.content,
        version_number=versions_count + 1,
        comment="Updated",
    )
    db.add(version)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(page, field, value)

    db.commit()
    db.refresh(page)
    return page


@router.delete("/pages/{page_id}")
def delete_page(workspace_slug: str, page_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    page = db.query(WikiPage).filter(WikiPage.id == page_id, WikiPage.workspace_id == ws.id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    if page.author_id != user.id and not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Permission denied")

    db.delete(page)
    db.commit()
    return {"message": "Page deleted"}


@router.get("/pages/{page_id}/versions", response_model=List[WikiPageVersionRead])
def list_versions(workspace_slug: str, page_id: UUID, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)
    page = db.query(WikiPage).filter(WikiPage.id == page_id, WikiPage.workspace_id == ws.id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return db.query(WikiPageVersion).filter(WikiPageVersion.page_id == page.id).order_by(WikiPageVersion.version_number.desc()).all()
