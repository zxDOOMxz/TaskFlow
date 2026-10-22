"""Revision ID: 002_chat_files_events
Revises: 001_initial
Create Date: 2026-10-14 00:00:00.000000

Добавляет таблицы, которые есть в models.py, но отсутствовали в 001_initial:
rooms, room_members, messages, files, events, event_participants,
а также индексы по внешним ключам горячих запросов.
Все операции идемпотентны: пропускаются, если объект уже существует.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_chat_files_events"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _existing_tables() -> set:
    return set(_inspector().get_table_names())


def _existing_indexes(table: str) -> set:
    insp = _inspector()
    if table not in insp.get_table_names():
        return set()
    return {i["name"] for i in insp.get_indexes(table)}


def upgrade() -> None:
    tables = _existing_tables()

    if "rooms" not in tables:
        op.create_table(
            "rooms",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=True),
            sa.Column("issue_id", sa.String(length=36), nullable=True),
            sa.Column("name", sa.String(length=100), nullable=True),
            sa.Column(
                "room_type",
                sa.Enum("direct", "group", "project", "issue", name="room_type"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["issue_id"], ["issues.id"], ondelete="CASCADE"),
        )

    if "room_members" not in tables:
        op.create_table(
            "room_members",
            sa.Column("room_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("room_id", "user_id"),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_room_members_user_id", "room_members", ["user_id"], unique=False)

    if "messages" not in tables:
        op.create_table(
            "messages",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("room_id", sa.String(length=36), nullable=False),
            sa.Column("author_id", sa.String(length=36), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("mentions", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        )
        op.create_index("ix_messages_room_id", "messages", ["room_id"], unique=False)
        op.create_index("ix_messages_author_id", "messages", ["author_id"], unique=False)

    if "files" not in tables:
        op.create_table(
            "files",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=True),
            sa.Column("uploaded_by_id", sa.String(length=36), nullable=False),
            sa.Column("original_name", sa.String(length=255), nullable=False),
            sa.Column("storage_key", sa.String(length=500), nullable=False),
            sa.Column("mime_type", sa.String(length=100), nullable=False),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("entity_type", sa.String(length=50), nullable=True),
            sa.Column("entity_id", sa.String(length=36), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"]),
        )
        op.create_index("ix_files_workspace_id", "files", ["workspace_id"], unique=False)

    if "events" not in tables:
        op.create_table(
            "events",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("workspace_id", sa.String(length=36), nullable=False),
            sa.Column("project_id", sa.String(length=36), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("timezone", sa.String(length=50), nullable=True),
            sa.Column("meeting_url", sa.String(length=500), nullable=True),
            sa.Column("created_by_id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        )

    if "event_participants" not in tables:
        op.create_table(
            "event_participants",
            sa.Column("event_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column(
                "status",
                sa.Enum("accepted", "tentative", "declined", name="participant_status"),
                nullable=True,
            ),
            sa.PrimaryKeyConstraint("event_id", "user_id"),
            sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        )

    # Индексы по FK горячих запросов (пропускаем существующие)
    wanted_indexes = [
        ("notifications", "ix_notifications_user_id", ["user_id"]),
        ("issues", "ix_issues_project_id", ["project_id"]),
        ("issues", "ix_issues_assignee_id", ["assignee_id"]),
        ("issue_comments", "ix_issue_comments_issue_id", ["issue_id"]),
        ("board_column_issues", "ix_board_column_issues_column_id", ["board_column_id"]),
    ]
    for table, name, columns in wanted_indexes:
        if table in _existing_tables() and name not in _existing_indexes(table):
            op.create_index(name, table, columns, unique=False)


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    tables = set(insp.get_table_names())
    wanted_indexes = [
        ("notifications", "ix_notifications_user_id"),
        ("issues", "ix_issues_project_id"),
        ("issues", "ix_issues_assignee_id"),
        ("issue_comments", "ix_issue_comments_issue_id"),
        ("board_column_issues", "ix_board_column_issues_column_id"),
    ]
    for table, name in wanted_indexes:
        if table in tables and name in {i["name"] for i in insp.get_indexes(table)}:
            op.drop_index(name, table_name=table)
    for table in ("event_participants", "events", "files", "messages", "room_members", "rooms"):
        if table in tables:
            op.drop_table(table)
