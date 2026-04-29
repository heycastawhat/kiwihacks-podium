"""add vote audit and team ops metadata

Adds vote timestamps/request metadata plus an append-only vote audit table.
"""

from alembic import op
import sqlalchemy as sa


revision = "a7c8d9e0f1b2"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "votes",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.add_column(
        "votes",
        sa.Column("ip_address", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "votes",
        sa.Column("user_agent", sa.String(length=500), nullable=False, server_default=""),
    )

    op.create_table(
        "vote_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("voter_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("vote_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("user_agent", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("reason", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["voter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vote_audit_logs_actor_id", "vote_audit_logs", ["actor_id"])
    op.create_index("ix_vote_audit_logs_created_at", "vote_audit_logs", ["created_at"])
    op.create_index("ix_vote_audit_logs_event_id", "vote_audit_logs", ["event_id"])
    op.create_index("ix_vote_audit_logs_project_id", "vote_audit_logs", ["project_id"])
    op.create_index("ix_vote_audit_logs_vote_id", "vote_audit_logs", ["vote_id"])
    op.create_index("ix_vote_audit_logs_voter_id", "vote_audit_logs", ["voter_id"])


def downgrade() -> None:
    op.drop_index("ix_vote_audit_logs_voter_id", table_name="vote_audit_logs")
    op.drop_index("ix_vote_audit_logs_vote_id", table_name="vote_audit_logs")
    op.drop_index("ix_vote_audit_logs_project_id", table_name="vote_audit_logs")
    op.drop_index("ix_vote_audit_logs_event_id", table_name="vote_audit_logs")
    op.drop_index("ix_vote_audit_logs_created_at", table_name="vote_audit_logs")
    op.drop_index("ix_vote_audit_logs_actor_id", table_name="vote_audit_logs")
    op.drop_table("vote_audit_logs")
    op.drop_column("votes", "user_agent")
    op.drop_column("votes", "ip_address")
    op.drop_column("votes", "created_at")
