import asyncio
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_workspace_member
from app.models import Issue, Message, Project, Room, RoomMember, User, WorkspaceMember
from app.mentions import create_mention_notifications
from app.routers.workspaces import get_workspace_by_slug, is_workspace_admin
from app.schemas.chat import MessageCreate, MessageRead, RoomCreate, RoomDetail, RoomRead
from app.websocket import broadcast_event

router = APIRouter()


def get_room(room_id: UUID, db: Session) -> Room:
    room = db.query(Room).filter(Room.id == str(room_id)).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.get("/rooms", response_model=List[RoomDetail])
async def list_rooms(
    workspace_slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    memberships = db.query(RoomMember).filter(RoomMember.user_id == user.id).all()
    room_ids = [m.room_id for m in memberships]
    rooms = db.query(Room).filter(Room.workspace_id == ws.id, Room.id.in_(room_ids)).all()

    result = []
    membership_map = {m.room_id: m for m in memberships}
    for room in rooms:
        last_message = (
            db.query(Message).filter(Message.room_id == room.id).order_by(Message.created_at.desc()).first()
        )
        member = membership_map.get(room.id)
        unread = 0
        if member:
            unread = db.query(Message).filter(
                Message.room_id == room.id,
                Message.created_at > (member.last_read_at or room.created_at),
            ).count()
        detail = RoomDetail.model_validate(room)
        detail.last_message = MessageRead.model_validate(last_message) if last_message else None
        detail.unread_count = unread
        result.append(detail)

    return result


@router.post("/rooms", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
async def create_room(
    workspace_slug: str,
    data: RoomCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    require_workspace_member(ws, user)

    if data.project_id:
        project = db.query(Project).filter(Project.id == str(data.project_id), Project.workspace_id == ws.id).first()
        if not project:
            raise HTTPException(status_code=400, detail="Project not in this workspace")
    if data.issue_id:
        issue = db.query(Issue).filter(Issue.id == str(data.issue_id)).first()
        if not issue or issue.project.workspace_id != ws.id:
            raise HTTPException(status_code=400, detail="Issue not in this workspace")

    member_ids = {user.id}
    for member_id in data.member_ids:
        if member_id == user.id:
            continue
        is_member = db.query(WorkspaceMember).filter(
            WorkspaceMember.workspace_id == ws.id, WorkspaceMember.user_id == str(member_id)
        ).first()
        if not is_member:
            raise HTTPException(status_code=400, detail="Member not in this workspace")
        member_ids.add(str(member_id))

    room = Room(
        workspace_id=ws.id,
        project_id=str(data.project_id) if data.project_id else None,
        issue_id=str(data.issue_id) if data.issue_id else None,
        name=data.name,
        room_type=data.room_type,
    )
    db.add(room)
    db.flush()

    for member_id in member_ids:
        db.add(RoomMember(room_id=room.id, user_id=member_id))

    db.commit()
    db.refresh(room)
    return room


@router.get("/rooms/{room_id}/messages", response_model=List[MessageRead])
async def list_messages(
    workspace_slug: str,
    room_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    room = get_room(room_id, db)
    if room.workspace_id != ws.id:
        raise HTTPException(status_code=404, detail="Room not found")

    member = db.query(RoomMember).filter(RoomMember.room_id == room.id, RoomMember.user_id == user.id).first()
    if not member and not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Not a room member")

    return (
        db.query(Message)
        .filter(Message.room_id == room.id)
        .order_by(Message.created_at.desc())
        .limit(100)
        .all()
    )


@router.post("/rooms/{room_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    workspace_slug: str,
    room_id: UUID,
    data: MessageCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = get_workspace_by_slug(workspace_slug, db)
    room = get_room(room_id, db)
    if room.workspace_id != ws.id:
        raise HTTPException(status_code=404, detail="Room not found")

    member = db.query(RoomMember).filter(RoomMember.user_id == user.id, RoomMember.room_id == room.id).first()
    if not member and not is_workspace_admin(ws, user):
        raise HTTPException(status_code=403, detail="Not a room member")

    message = Message(room_id=room.id, author_id=user.id, content=data.content)
    db.add(message)
    db.commit()
    db.refresh(message)

    asyncio.create_task(
        # mode="json": UUID/datetime сериализуются в строки, иначе json.dumps в WebSocket падает
        broadcast_event(f"room:{room.id}", "new_message", MessageRead.model_validate(message).model_dump(mode="json"))
    )

    create_mention_notifications(
        db,
        data.content,
        user,
        ws.id,
        "message",
        message.id,
        f"чате {room.name or 'без названия'}",
    )

    return message
