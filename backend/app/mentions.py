import re
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Issue, Notification, User, WikiPage


def parse_mentions(content: str) -> Dict[str, List[str]]:
    if not content:
        return {"users": [], "issues": [], "pages": []}

    user_mentions = re.findall(r"@([a-zA-Z0-9_.@-]+)", content)
    issue_mentions = re.findall(r"#([A-Z][A-Z0-9]*-\d+)", content)
    page_mentions = re.findall(r"\[\[([^\]]+)\]\]", content)

    return {
        "users": list(set(user_mentions)),
        "issues": list(set(issue_mentions)),
        "pages": list(set(page_mentions)),
    }


def find_mentioned_users(db: Session, workspace_id: UUID, handles: List[str]) -> List[User]:
    if not handles:
        return []

    users = []
    for handle in handles:
        # Try exact email
        user = db.query(User).filter(User.email == handle).first()
        if not user:
            # Try email prefix
            user = db.query(User).filter(User.email.ilike(f"{handle}@%")).first()
        if not user:
            # Try first name
            user = (
                db.query(User)
                .join(User.workspaces)
                .filter(
                    User.first_name.ilike(handle),
                    User.workspaces.any(workspace_id=workspace_id),
                )
                .first()
            )
        if user:
            users.append(user)

    return list({u.id: u for u in users}.values())


def create_mention_notifications(
    db: Session,
    content: str,
    author: User,
    workspace_id: UUID,
    entity_type: str,
    entity_id: UUID,
    entity_title: str,
):
    mentions = parse_mentions(content)
    users = find_mentioned_users(db, workspace_id, mentions["users"])

    for user in users:
        if user.id == author.id:
            continue
        notification = Notification(
            user_id=user.id,
            type="mention",
            title=f"Упоминание от {author.first_name} {author.last_name}",
            content=f"Вас упомянули в {entity_type}: {entity_title}",
            entity_type=entity_type,
            entity_id=entity_id,
        )
        db.add(notification)

    db.commit()
    return users


def resolve_mention_links(db: Session, content: str, workspace_id: UUID) -> Dict[str, List[dict]]:
    """Resolve mentioned issues and pages to their IDs for frontend."""
    mentions = parse_mentions(content)

    issues = []
    for key in mentions["issues"]:
        project_key = key.split("-")[0]
        issue = (
            db.query(Issue)
            .join(Issue.project)
            .filter(Issue.key == key.upper(), Issue.project.has(workspace_id=workspace_id))
            .first()
        )
        if issue:
            issues.append({"key": issue.key, "id": str(issue.id), "title": issue.title})

    pages = []
    for title in mentions["pages"]:
        page = (
            db.query(WikiPage)
            .filter(WikiPage.workspace_id == workspace_id, WikiPage.title.ilike(title))
            .first()
        )
        if page:
            pages.append({"id": str(page.id), "title": page.title, "slug": page.slug})

    return {"issues": issues, "pages": pages}
