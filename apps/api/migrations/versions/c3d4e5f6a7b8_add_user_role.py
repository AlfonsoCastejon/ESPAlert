"""Añade campo role a la tabla users.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-14
"""

from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None

user_role_enum = sa.Enum("user", "admin", name="user_role")


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
    )


def downgrade() -> None:
    op.drop_column("users", "role")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
