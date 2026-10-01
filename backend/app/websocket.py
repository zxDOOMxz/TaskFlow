import json
from typing import Dict, List

from fastapi import WebSocket, WebSocketDisconnect

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


async def websocket_endpoint(websocket: WebSocket, room_id: str, token: str):
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")
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
