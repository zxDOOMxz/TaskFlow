from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, boards, chat, contact, files, issues, notifications, projects, search, sprints, wiki, workspaces
from app.websocket import websocket_endpoint

settings = get_settings()

app = FastAPI(
    title="TaskFlow API",
    description="Task tracker + Wiki knowledge base MVP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
app.include_router(projects.router, prefix="/api/v1/workspaces/{workspace_slug}/projects", tags=["projects"])
app.include_router(issues.router, prefix="/api/v1/projects/{project_key}/issues", tags=["issues"])
app.include_router(boards.router, prefix="/api/v1/projects/{project_key}/boards", tags=["boards"])
app.include_router(sprints.router, prefix="/api/v1/projects/{project_key}/sprints", tags=["sprints"])
app.include_router(wiki.router, prefix="/api/v1/workspaces/{workspace_slug}/wiki", tags=["wiki"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(chat.router, prefix="/api/v1/workspaces/{workspace_slug}/chat", tags=["chat"])
app.include_router(files.router, prefix="/api/v1/workspaces/{workspace_slug}/files", tags=["files"])
app.include_router(contact.router, prefix="/api/v1", tags=["contact"])


@app.websocket("/ws/{room_id}")
async def websocket_route(websocket: WebSocket, room_id: str, token: str):
    await websocket_endpoint(websocket, room_id, token)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "TaskFlow API", "docs": "/docs"}
