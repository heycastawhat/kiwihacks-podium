"""Add global admin role and permission storage.

Users:
- add is_admin
- add admin_permissions_csv
"""

from alembic import op
import sqlalchemy as sa

revision = "f1a2b3c4d5e6"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column(
            "admin_permissions_csv",
            sa.String(length=1000),
            nullable=False,
            server_default="",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "admin_permissions_csv")
    op.drop_column("users", "is_admin")
