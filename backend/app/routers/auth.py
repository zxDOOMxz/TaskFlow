import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import RefreshToken, User, Workspace, WorkspaceMember
from app.schemas.auth import (
    PasswordChange,
    RefreshTokenRequest,
    TokenPair,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.supabase_auth_client import SupabaseAuthError, SupabaseAuthClient

router = APIRouter()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_default_workspace_data(workspace_id: UUID):
    from app.models import IssuePriority, IssueStatus, IssueType

    return [
        IssueType(workspace_id=workspace_id, name="Epic", color="#905cff", is_default=True),
        IssueType(workspace_id=workspace_id, name="Story", color="#65ba43", is_default=True),
        IssueType(workspace_id=workspace_id, name="Task", color="#4bade8", is_default=True),
        IssueType(workspace_id=workspace_id, name="Bug", color="#e9493a", is_default=True),
        IssueType(workspace_id=workspace_id, name="Subtask", color="#4bade8", is_default=True),
        IssueStatus(workspace_id=workspace_id, name="To Do", category="todo", color="#dfe1e6", position=0, is_default=True),
        IssueStatus(workspace_id=workspace_id, name="In Progress", category="in_progress", color="#0052cc", position=1, is_default=True),
        IssueStatus(workspace_id=workspace_id, name="Review", category="in_progress", color="#ff991f", position=2, is_default=True),
        IssueStatus(workspace_id=workspace_id, name="Done", category="done", color="#0b875b", position=3, is_default=True),
        IssuePriority(workspace_id=workspace_id, name="Blocker", color="#e9493a", is_default=True),
        IssuePriority(workspace_id=workspace_id, name="Critical", color="#e97b3a", is_default=True),
        IssuePriority(workspace_id=workspace_id, name="Major", color="#ffab00", is_default=True),
        IssuePriority(workspace_id=workspace_id, name="Minor", color="#4bade8", is_default=True),
        IssuePriority(workspace_id=workspace_id, name="Trivial", color="#8993a4", is_default=True),
    ]


def _create_local_user_and_workspace(
    db: Session,
    user_id: str,
    email: str,
    first_name: str,
    last_name: str,
):
    user = User(
        id=user_id,
        email=email,
        hashed_password="",
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )
    db.add(user)
    db.flush()

    slug_base = f"{first_name.lower()}-{last_name.lower()}"
    slug = slug_base
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    workspace = Workspace(name=f"{first_name}'s Workspace", slug=slug, owner_id=user.id)
    db.add(workspace)
    db.flush()
    db.add_all(create_default_workspace_data(workspace.id))
    db.commit()
    db.refresh(user)
    return user


@router.post("/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(
    data: UserCreate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.is_supabase_enabled:
        auth_client = SupabaseAuthClient(settings)
        try:
            session = auth_client.sign_up(
                email=data.email,
                password=data.password,
                user_metadata={
                    "first_name": data.first_name,
                    "last_name": data.last_name,
                },
            )
        except SupabaseAuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        user_data = session.get("user", {})
        user_id = user_data.get("id")
        if not user_id:
            raise HTTPException(status_code=500, detail="Supabase did not return a user id")

        existing = db.query(User).filter(User.id == user_id).first()
        if not existing:
            _create_local_user_and_workspace(
                db,
                user_id=user_id,
                email=data.email,
                first_name=data.first_name,
                last_name=data.last_name,
            )

        return {
            "access_token": session["session"]["access_token"],
            "refresh_token": session["session"]["refresh_token"],
        }

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
    )
    db.add(user)
    db.flush()

    slug_base = f"{data.first_name.lower()}-{data.last_name.lower()}"
    slug = slug_base
    counter = 1
    while db.query(Workspace).filter(Workspace.slug == slug).first():
        slug = f"{slug_base}-{counter}"
        counter += 1

    workspace = Workspace(name=f"{data.first_name}'s Workspace", slug=slug, owner_id=user.id)
    db.add(workspace)
    db.flush()

    db.add_all(create_default_workspace_data(workspace.id))

    db.commit()
    db.refresh(user)

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    store_refresh_token(db, user.id, refresh)

    return {"access_token": access, "refresh_token": refresh}


@router.post("/login", response_model=TokenPair)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.is_supabase_enabled:
        auth_client = SupabaseAuthClient(settings)
        try:
            session = auth_client.sign_in(email=data.email, password=data.password)
        except SupabaseAuthError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        user_data = session.get("user", {})
        user_id = user_data.get("id")
        if user_id:
            existing = db.query(User).filter(User.id == user_id).first()
            if not existing:
                metadata = user_data.get("user_metadata", {})
                _create_local_user_and_workspace(
                    db,
                    user_id=user_id,
                    email=data.email,
                    first_name=metadata.get("first_name", ""),
                    last_name=metadata.get("last_name", ""),
                )

        return {
            "access_token": session["session"]["access_token"],
            "refresh_token": session["session"]["refresh_token"],
        }

    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})
    store_refresh_token(db, user.id, refresh)

    return {"access_token": access, "refresh_token": refresh}


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    token_hash = hash_token(data.refresh_token)
    stored = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > datetime.now(timezone.utc),
    ).first()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    stored.revoked_at = datetime.now(timezone.utc)
    db.commit()

    access = create_access_token({"sub": user_id})
    refresh = create_refresh_token({"sub": user_id})
    store_refresh_token(db, UUID(user_id), refresh)

    return {"access_token": access, "refresh_token": refresh}


@router.post("/logout")
def logout(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_hash = hash_token(data.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if stored:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()
    return {"message": "Logged out"}


@router.post("/logout-all")
def logout_all(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).update(
        {RefreshToken.revoked_at: datetime.now(timezone.utc)}
    )
    db.commit()
    return {"message": "All sessions revoked"}


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user


@router.put("/me", response_model=UserRead)
def update_me(data: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    allowed = {"first_name", "last_name", "timezone", "avatar_url"}
    for key, value in data.items():
        if key in allowed:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password")
def change_password(data: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(data.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    user.hashed_password = get_password_hash(data.new_password)
    db.commit()
    return {"message": "Password updated"}


def store_refresh_token(db: Session, user_id: UUID, token: str):
    token_hash = hash_token(token)
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    rt = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires)
    db.add(rt)
    db.commit()
