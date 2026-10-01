from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.models import User
from app.security import decode_token

security = HTTPBearer(auto_error=False)


def _get_local_user(token: str, db: Session) -> User:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if settings.is_supabase_enabled:
        from app.supabase_auth import decode_supabase_token

        payload = decode_supabase_token(credentials.credentials, settings)
        if payload:
            user_id = payload.get("sub")
            email = payload.get("email")
            if user_id and email:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    user = User(
                        id=user_id,
                        email=email,
                        hashed_password="",
                        first_name=payload.get("user_metadata", {}).get("first_name", ""),
                        last_name=payload.get("user_metadata", {}).get("last_name", ""),
                        is_active=True,
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                elif user.is_active:
                    return user

    return _get_local_user(credentials.credentials, db)


def require_workspace_member(workspace, user: User):
    member = next((m for m in workspace.members if m.user_id == user.id), None)
    if not member and workspace.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")
    return member


def require_project_member(project, user: User):
    member = next((m for m in project.members if m.user_id == user.id), None)
    if not member and project.lead_id != user.id:
        from app.routers.workspaces import is_workspace_admin
        ws_member = is_workspace_admin(project.workspace, user)
        if not ws_member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")
    return member
