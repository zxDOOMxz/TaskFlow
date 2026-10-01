import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default="Europe/Moscow")
    is_active = Column(Boolean, default=True)
    is_superadmin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    workspaces = relationship("WorkspaceMember", back_populates="user")
    owned_workspaces = relationship("Workspace", back_populates="owner")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    owner = relationship("User", back_populates="owned_workspaces")
    members = relationship("WorkspaceMember", back_populates="workspace")
    projects = relationship("Project", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("admin", "manager", "developer", "viewer", name="workspace_role"), default="developer")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="workspaces")

    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uix_workspace_user"),)


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    lead_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    icon = Column(String(50), nullable=True)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    workspace = relationship("Workspace", back_populates="projects")
    lead = relationship("User")
    members = relationship("ProjectMember", back_populates="project")
    issues = relationship("Issue", back_populates="project")

    __table_args__ = (UniqueConstraint("workspace_id", "key", name="uix_workspace_project_key"),)


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("admin", "manager", "developer", "viewer", name="project_role"), default="developer")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    project = relationship("Project", back_populates="members")
    user = relationship("User")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uix_project_user"),)


class IssueType(Base):
    __tablename__ = "issue_types"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    is_default = Column(Boolean, default=False)

    workspace = relationship("Workspace")


class IssueStatus(Base):
    __tablename__ = "issue_statuses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    category = Column(Enum("todo", "in_progress", "done", name="issue_status_category"), default="todo")
    color = Column(String(20), nullable=True)
    position = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)

    workspace = relationship("Workspace")


class IssuePriority(Base):
    __tablename__ = "issue_priorities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    is_default = Column(Boolean, default=False)

    workspace = relationship("Workspace")


class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    goal = Column(Text, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum("planning", "active", "completed", "closed", name="sprint_status"), default="planning")
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    project = relationship("Project")
    issues = relationship("Issue", back_populates="sprint")


class Issue(Base):
    __tablename__ = "issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    sprint_id = Column(String(36), ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    parent_id = Column(String(36), ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    issue_type_id = Column(String(36), ForeignKey("issue_types.id"), nullable=False)
    issue_status_id = Column(String(36), ForeignKey("issue_statuses.id"), nullable=False)
    issue_priority_id = Column(String(36), ForeignKey("issue_priorities.id"), nullable=False)
    reporter_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    assignee_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    key = Column(String(20), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    story_points = Column(Integer, nullable=True)
    original_estimate_minutes = Column(Integer, nullable=True)
    remaining_estimate_minutes = Column(Integer, nullable=True)
    logged_time_minutes = Column(Integer, default=0)
    due_date = Column(DateTime(timezone=True), nullable=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    project = relationship("Project", back_populates="issues")
    sprint = relationship("Sprint", back_populates="issues")
    parent = relationship("Issue", remote_side=[id], backref="subtasks")
    issue_type = relationship("IssueType")
    issue_status = relationship("IssueStatus")
    issue_priority = relationship("IssuePriority")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    comments = relationship("IssueComment", back_populates="issue", order_by="IssueComment.created_at")
    time_logs = relationship("IssueTimeLog", back_populates="issue", order_by="IssueTimeLog.created_at")

    __table_args__ = (UniqueConstraint("project_id", "key", name="uix_project_issue_key"),)


class IssueLink(Base):
    __tablename__ = "issue_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    target_issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    link_type = Column(Enum("blocks", "depends_on", "duplicates", "relates_to", name="issue_link_type"), default="relates_to")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    source_issue = relationship("Issue", foreign_keys=[source_issue_id])
    target_issue = relationship("Issue", foreign_keys=[target_issue_id])


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    issue = relationship("Issue", back_populates="comments")
    author = relationship("User")


class IssueTimeLog(Base):
    __tablename__ = "issue_time_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    minutes = Column(Integer, nullable=False)
    description = Column(String(500), nullable=True)
    logged_at = Column(DateTime(timezone=True), default=now_utc)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    issue = relationship("Issue", back_populates="time_logs")
    user = relationship("User")


class Board(Base):
    __tablename__ = "boards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    board_type = Column(Enum("kanban", "scrum", name="board_type"), default="kanban")
    filter_query = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    project = relationship("Project")
    columns = relationship("BoardColumn", back_populates="board", order_by="BoardColumn.position")


class BoardColumn(Base):
    __tablename__ = "board_columns"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = Column(String(36), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    issue_status_id = Column(String(36), ForeignKey("issue_statuses.id"), nullable=True)
    name = Column(String(50), nullable=False)
    position = Column(Integer, default=0)
    wip_limit = Column(Integer, nullable=True)

    board = relationship("Board", back_populates="columns")
    issue_status = relationship("IssueStatus")
    issues = relationship("BoardColumnIssue", back_populates="column", order_by="BoardColumnIssue.position")


class BoardColumnIssue(Base):
    __tablename__ = "board_column_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_column_id = Column(String(36), ForeignKey("board_columns.id", ondelete="CASCADE"), nullable=False)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer, default=0)

    column = relationship("BoardColumn", back_populates="issues")
    issue = relationship("Issue")

    __table_args__ = (UniqueConstraint("board_column_id", "issue_id", name="uix_column_issue"),)


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("wiki_pages.id", ondelete="SET NULL"), nullable=True)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    position = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    workspace = relationship("Workspace")
    parent = relationship("WikiPage", remote_side=[id], backref="children")
    author = relationship("User")

    __table_args__ = (UniqueConstraint("workspace_id", "slug", name="uix_workspace_page_slug"),)


class WikiPageVersion(Base):
    __tablename__ = "wiki_page_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    page_id = Column(String(36), ForeignKey("wiki_pages.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    version_number = Column(Integer, nullable=False)
    comment = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    page = relationship("WikiPage")
    author = relationship("User")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(Enum("mention", "assigned", "comment", "status_change", "invite", name="notification_type"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    entity_type = Column(Enum("issue", "page", "message", "project", name="entity_type"), nullable=True)
    entity_id = Column(String(36), nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    read_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    issue_id = Column(String(36), ForeignKey("issues.id", ondelete="CASCADE"), nullable=True)
    name = Column(String(100), nullable=True)
    room_type = Column(Enum("direct", "group", "project", "issue", name="room_type"), default="group")
    created_at = Column(DateTime(timezone=True), default=now_utc)

    workspace = relationship("Workspace")
    project = relationship("Project")
    issue = relationship("Issue")


class RoomMember(Base):
    __tablename__ = "room_members"

    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    room = relationship("Room")
    user = relationship("User")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_id = Column(String(36), ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    mentions = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    room = relationship("Room")
    author = relationship("User")


class File(Base):
    __tablename__ = "files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    original_name = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, default=0)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc)

    workspace = relationship("Workspace")
    uploaded_by = relationship("User")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    end_at = Column(DateTime(timezone=True), nullable=False)
    timezone = Column(String(50), default="Europe/Moscow")
    meeting_url = Column(String(500), nullable=True)
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    workspace = relationship("Workspace")
    created_by = relationship("User")


class EventParticipant(Base):
    __tablename__ = "event_participants"

    event_id = Column(String(36), ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    status = Column(Enum("accepted", "tentative", "declined", name="participant_status"), default="accepted")

    event = relationship("Event")
    user = relationship("User")
