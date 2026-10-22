import json
from typing import Dict, List, Optional

from fastapi import WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.database import SessionLocal
from app.models import Project, Room, RoomMember, User
from app.security import decode_token


class ConnectionManager:
    def __init__(self):
        # room_id -> list of (websocket, user_id)
        self.active_connections: Dict[str, List[tuple]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id] = [
                (ws, uid) for ws, uid in self.active_connections[room_id] if ws != websocket
            ]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id not in self.active_connections:
            return
        payload = json.dumps(message)
        disconnected = []
        for websocket, _ in self.active_connections[room_id]:
            try:
                await websocket.send_text(payload)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket, room_id)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_text(json.dumps(message))


manager = ConnectionManager()


def _decode_ws_token(token: str) -> Optional[dict]:
    """Сначала Supabase JWT (основной flow), затем локальный access-токен."""
    settings = get_settings()
    if settings.is_supabase_enabled:
        from app.supabase_auth import decode_supabase_token

        payload = decode_supabase_token(token, settings)
        if payload:
            return payload
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload
    return None


def _can_access_room(room_id: str, user: User) -> bool:
    """room:<uuid> — участник комнаты или админ workspace; project:<uuid> — участник workspace."""
    db = SessionLocal()
    try:
        if room_id.startswith("room:"):
            room = db.query(Room).filter(Room.id == room_id[len("room:"):]).first()
            if not room:
                return False
            member = db.query(RoomMember).filter(RoomMember.room_id == room.id, RoomMember.user_id == user.id).first()
            if member:
                return True
            return room.workspace.owner_id == user.id or any(
                m.user_id == user.id and m.role == "admin" for m in room.workspace.members
            )
        if room_id.startswith("project:"):
            project = db.query(Project).filter(Project.id == room_id[len("project:"):]).first()
            if not project:
                return False
            return project.workspace.owner_id == user.id or any(
                m.user_id == user.id for m in project.workspace.members
            )
        return False
    finally:
        db.close()


async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    payload = _decode_ws_token(token)
    user_id = payload.get("sub") if payload else None
    if not payload or not user_id:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()
    if not user or not user.is_active:
        await websocket.close(code=1008)
        return

    if not _can_access_room(room_id, user):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                await manager.broadcast(room_id, {
                    "type": "message",
                    "user_id": user_id,
                    "data": message,
                })
            except json.JSONDecodeError:
                await manager.send_personal(websocket, {"type": "error", "detail": "Invalid JSON"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)


async def broadcast_event(room_id: str, event_type: str, data: dict):
    await manager.broadcast(room_id, {"type": event_type, "data": data})
