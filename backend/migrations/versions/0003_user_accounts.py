"""user accounts + user_id on url_checks (U2)

Revision ID: 0003_user_accounts
Revises: 0002_ip_asn_reputation
Create Date: 2026-06-08

Adds the ``users`` table and a nullable ``user_id`` foreign-key column on
``url_checks``.  On a FRESH database these already exist from ``create_all``
in the baseline migration, so all ``create_*`` calls use ``checkfirst=True``.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_user_accounts"
down_revision = "0002_ip_asn_reputation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    # Create user_role_enum (PostgreSQL only; SQLite uses VARCHAR).
    if is_pg:
        user_role_enum = sa.Enum("user", "admin", name="user_role_enum")
        user_role_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column("display_name", sa.String(128), server_default=""),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role_enum", create_constraint=False),
            server_default="user",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("check_count", sa.Integer(), server_default="0"),
        if_not_exists=True,
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True, if_not_exists=True)
    op.create_index("ix_users_role", "users", ["role"], if_not_exists=True)
    op.create_index("ix_users_created_at", "users", ["created_at"], if_not_exists=True)

    # Add user_id FK to url_checks — guard against create_all having already run.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("url_checks")}
    if "user_id" not in existing_cols:
        with op.batch_alter_table("url_checks") as batch_op:
            batch_op.add_column(
                sa.Column("user_id", sa.Uuid(as_uuid=True), nullable=True),
            )

    op.create_index(
        "ix_url_checks_user_id", "url_checks", ["user_id"], if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index("ix_url_checks_user_id", table_name="url_checks", if_exists=True)
    with op.batch_alter_table("url_checks") as batch_op:
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_created_at", table_name="users", if_exists=True)
    op.drop_index("ix_users_role", table_name="users", if_exists=True)
    op.drop_index("ix_users_email", table_name="users", if_exists=True)
    op.drop_table("users")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        sa.Enum(name="user_role_enum").drop(bind, checkfirst=True)
