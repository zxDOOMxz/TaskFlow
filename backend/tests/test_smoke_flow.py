"""Регрессионный смоук-тест ключевых сценариев API.

Покрывает баги, найденные при моделировании:
- фильтры по String(36)-колонкам с UUID-параметрами (комнаты, файлы, доски);
- сериализация created_at в FileReadSchema;
- наличие колонок у GET /projects/{key}/boards (рендер доски на фронте);
- проверки членства (файлы, чат, задачи) для посторонних пользователей;
- отклонение WebSocket-подключений к чужим/несуществующим комнатам.
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


@pytest.fixture
def second_client(client):
    """Неавторизованный клиент второго пользователя."""
    return TestClient(app)


@pytest.fixture
def storage_stub(monkeypatch):
    """Без Supabase/MinIO в тестах: подменяем функции хранилища."""
    import app.routers.files as files_router

    monkeypatch.setattr(files_router, "upload_file", lambda **kw: "files/fake.txt")
    monkeypatch.setattr(files_router, "get_presigned_url", lambda *a, **k: "https://example.com/signed")
    monkeypatch.setattr(files_router, "delete_file", lambda *a, **k: None)


@pytest.fixture
def ws_test_env(monkeypatch):
    """websocket.py использует SessionLocal/get_settings напрямую, а не через Depends:
    в тестах подменяем их на тестовую sqlite-базу и локальную аутентификацию."""
    from app.config import Settings
    from tests.conftest import TEST_DATABASE_URL, TestingSessionLocal

    test_settings = Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key",
        supabase_enabled=False,
    )
    monkeypatch.setattr("app.websocket.get_settings", lambda: test_settings)
    monkeypatch.setattr("app.websocket.SessionLocal", TestingSessionLocal)


def test_full_flow(auth_client, second_client, storage_stub, ws_test_env):
    client = auth_client

    # Workspace создан при регистрации
    workspaces = client.get("/api/v1/workspaces").json()
    assert len(workspaces) == 1
    slug = workspaces[0]["slug"]

    # Проект
    r = client.post(f"/api/v1/workspaces/{slug}/projects", json={"key": "TF", "name": "TaskFlow"})
    assert r.status_code == 201

    # Доска с колонками (критично для фронта)
    boards = client.get("/api/v1/projects/TF/boards").json()
    assert boards and "columns" in boards[0] and len(boards[0]["columns"]) > 0

    # Задача
    r = client.post("/api/v1/projects/TF/issues", json={"title": "Первая задача"})
    assert r.status_code == 201
    issue = r.json()
    assert issue["key"] == "TF-1"

    # Комментарий
    assert client.post(f"/api/v1/projects/TF/issues/{issue['key']}/comments",
                       json={"content": "Комментарий"}).status_code == 201

    # Чат: комната + сообщение (UUID-фильтры по String-колонкам)
    r = client.post(f"/api/v1/workspaces/{slug}/chat/rooms",
                    json={"room_type": "group", "name": "General"})
    assert r.status_code == 201
    room = r.json()
    assert client.post(f"/api/v1/workspaces/{slug}/chat/rooms/{room['id']}/messages",
                       json={"content": "Привет"}).status_code == 201
    assert len(client.get(f"/api/v1/workspaces/{slug}/chat/rooms/{room['id']}/messages").json()) == 1

    # Файлы (загрузка без MinIO — через storage_stub)
    assert client.get(f"/api/v1/workspaces/{slug}/files").json() == []
    r = client.post(f"/api/v1/workspaces/{slug}/files/upload",
                    files={"file": ("test.txt", b"hello", "text/plain")})
    assert r.status_code == 201
    assert r.json()["original_name"] == "test.txt"

    # Поиск, включая экранирование wildcards
    results = client.get("/api/v1/search", params={"q": "Первая", "workspace_slug": slug}).json()
    assert any(item["type"] == "issue" for item in results)
    assert client.get("/api/v1/search", params={"q": "100%_х", "workspace_slug": slug}).status_code == 200

    # Второй пользователь не имеет доступа
    other = second_client
    assert other.post("/api/v1/auth/register", json={
        "email": "other@example.com", "password": "password123",
        "first_name": "Other", "last_name": "User",
    }).status_code == 201
    other_login = other.post("/api/v1/auth/login", json={
        "email": "other@example.com", "password": "password123",
    }).json()
    other.headers["Authorization"] = f"Bearer {other_login['access_token']}"

    assert other.get(f"/api/v1/workspaces/{slug}/files").status_code == 403
    assert other.get("/api/v1/projects/TF/issues").status_code == 403
    assert other.get(f"/api/v1/workspaces/{slug}/chat/rooms/{room['id']}/messages").status_code == 403
    assert other.post(f"/api/v1/workspaces/{slug}/chat/rooms",
                      json={"room_type": "group", "name": "Hack"}).status_code == 403

    # WebSocket: участник — ок, неизвестная комната — отказ
    token = client.headers["Authorization"].split(" ")[1]
    with client.websocket_connect(f"/ws/room:{room['id']}?token={token}") as ws:
        ws.send_text('{"hello":"world"}')
        data = ws.receive_json()
        assert data["type"] == "message"

    unknown = f"room:{uuid.uuid4()}"
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws/{unknown}?token={token}"):
            pass
